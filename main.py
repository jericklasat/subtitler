import sys
import os
import mlx_whisper

def format_timestamp(seconds):
    """Converts seconds (float) to standard SRT time format: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int(round((seconds % 1) * 1000))
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

def main():
    # 1. Validation check for argument lengths
    if len(sys.argv) < 2:
        print("Error: Missing arguments.")
        print("\n LOCAL MODE USAGE:")
        print("  python3 subtitler.py /path/to/local_video.mp4 [language] [task]")
        print("\n SSH STREAM MODE USAGE:")
        print("  ssh ... | python3 subtitler.py - [language] [task] [output_name.srt]")
        return

    first_arg = sys.argv[1]

    # 2. DETECT MODE: Is the first argument a real file path on your local Mac?
    if os.path.exists(first_arg) and first_arg != "-":
        # === LOCAL VIDEO MODE ===
        video_input = first_arg
        language = sys.argv[2] if len(sys.argv) > 2 else "ja"
        task = sys.argv[3] if len(sys.argv) > 3 else "translate"
        
        base_path, _ = os.path.splitext(video_input)
        srt_path = base_path + ".srt"
        
        print(f" [Local Mode] Processing: {os.path.basename(video_input)}")

    elif first_arg == "-":
        # === SSH STREAM MODE ===
        if len(sys.argv) < 5:
            print("Error: Stream mode requires target settings.")
            print("Usage: ssh ... | python3 subtitler.py - [language] [task] [output_name.srt]")
            return
            
        video_input = "-" 
        language = sys.argv[2]
        task = sys.argv[3]
        srt_path = sys.argv[4]
        
        print(f"[SSH Stream Mode] Intercepting network audio channel...")
    else:
        print(f"Error: Local file not found at '{first_arg}'.")
        print("If you are trying to stream over SSH, make sure your first argument is a dash '-'")
        return

    print(f"Settings: Language='{language}' | Task='{task}' | Exporting to='{srt_path}'")
    print("Running Whisper Large-V3-MLX with Apple Silicon M4 acceleration...")

    try:
        # 3. Core Whisper execution (shared by both modes)
        result = mlx_whisper.transcribe(
            video_input, 
            path_or_hf_repo="mlx-community/whisper-large-v3-mlx",
            verbose=True,
            language=language,
            task=task,
            compression_ratio_threshold=2.4,
            no_speech_threshold=0.6,
            # Prevents Whisper from conditioning each window on prior output,
            # which otherwise causes repetition loops (see mlx_whisper --condition-on-previous-text False).
            condition_on_previous_text=False,
        )
        
        segments = result.get("segments", [])
        if not segments:
            print("No speech resolved from the media input.")
            return

        srt_lines = []
        recent_phrases = []
        last_valid_end_time = 0.0  
        consecutive_repeat_count = 0  # Tracks how many times a phrase loops consecutively
        last_cleaned_text = ""        # Normalizes strings to track strict repetition loops
        counter = 1

        for segment in segments:
            text = segment["text"].strip().lower().replace(".", "").replace(",", "").replace("!", "").replace("?", "")
            raw_text = segment["text"].strip()
            
            if not text:
                continue

            # ANTI-LOOP GATEWAY 1: Drop zero-duration timestamps
            if segment["start"] == segment["end"]:
                continue

            # ANTI-LOOP GATEWAY 2: CRITICAL CONSECUTIVE REPETITION LOCK
            if text == last_cleaned_text:
                consecutive_repeat_count += 1
            else:
                consecutive_repeat_count = 1
                last_cleaned_text = text

            # Drop consecutive duplicates as a safety net when Whisper still loops.
            if consecutive_repeat_count > 1:
                continue
                
            # ANTI-LOOP GATEWAY 3: Drop rolling window text loops
            if recent_phrases.count(text) >= 2 or any(text in past or past in text for past in recent_phrases[-2:] if past):
                continue

            # ANTI-LOOP GATEWAY 4: CRITICAL TIME-LOCK
            if segment["start"] < last_valid_end_time:
                continue

            start = format_timestamp(segment["start"])
            end = format_timestamp(segment["end"])
            
            srt_lines.append(f"{counter}\n{start} --> {end}\n{raw_text}\n\n")
            
            # Update markers only when a row successfully passes all sanity checks
            last_valid_end_time = segment["end"]
            
            recent_phrases.append(text)
            if len(recent_phrases) > 5:
                recent_phrases.pop(0)
                
            counter += 1
        
        with open(srt_path, "w", encoding="utf-8") as f:
            f.writelines(srt_lines)
            
        print(f"\n Finished! Subtitles successfully saved to: {srt_path}")
        
    except Exception as e:
        print(f"\n Error encountered: {e}")

if __name__ == "__main__":
    main()

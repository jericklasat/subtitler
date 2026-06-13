# Subtitler

Generate SRT subtitle files from video or audio using [Whisper Large V3](https://huggingface.co/mlx-community/whisper-large-v3-mlx) on Apple Silicon, accelerated with [MLX](https://github.com/ml-explore/mlx).

The script transcribes speech, applies filters to reduce Whisper repetition loops, and writes a standard `.srt` file.

## Requirements

- **macOS** with **Apple Silicon** (M1 / M2 / M3 / M4 /M5)
- **Python 3.8+**
- **ffmpeg** (for audio extraction from video files)

Install ffmpeg with Homebrew:

```bash
brew install ffmpeg
```

## Setup

Clone the repository and create a virtual environment:

```bash
git clone https://github.com/jericklasat/subtitler.git
cd subtitler

python3 -m venv .venv
source .venv/bin/activate
pip install mlx-whisper
```

On first run, the Whisper model (`mlx-community/whisper-large-v3-mlx`, ~3.1 GB) is downloaded automatically from Hugging Face.

## Usage

### Local file mode

Point the script at a video or audio file on disk. The output SRT is written next to the input file with the same basename.

```bash
python3 main.py /path/to/video.mp4
```

**Arguments:**

| Argument   | Required | Default     | Description                                                     |
| ---------- | -------- | ----------- | --------------------------------------------------------------- |
| `input`    | Yes      | —           | Path to a local video or audio file                             |
| `language` | No       | `ja`        | Source language code (e.g. `ja`, `en`, `ko`)                    |
| `task`     | No       | `translate` | `translate` (to English) or `transcribe` (keep source language) |

**Examples:**

```bash
# Japanese video → English subtitles (default)
python3 main.py ~/Movies/episode.mp4

# Japanese video → Japanese subtitles
python3 main.py ~/Movies/episode.mp4 ja transcribe

# English video → English subtitles
python3 main.py ~/Movies/talk.mp4 en transcribe
```

Output: `~/Movies/episode.srt`

### SSH stream mode

Pipe audio from a remote machine over SSH. Useful when the media lives on another host and you want to transcribe on your Mac.

```bash
ssh user@remote-host "ffmpeg -i /path/to/video.mp4 -vn -af 'highpass=f=200,lowpass=f=3000,afftdn' -f wav -ar 16000 -ac 1 -" | python3 main.py - ja translate output.srt
```

**Arguments:**

| Argument     | Required | Description                               |
| ------------ | -------- | ----------------------------------------- |
| `-`          | Yes      | Tells the script to read audio from stdin |
| `language`   | Yes      | Source language code                      |
| `task`       | Yes      | `translate` or `transcribe`               |
| `output.srt` | Yes      | Path where the SRT file should be saved   |

## How it works

1. **Transcription** — `mlx_whisper.transcribe()` runs Whisper Large V3 with MLX on Apple Silicon.
2. **Anti-loop filtering** — Segments that Whisper sometimes repeats (zero-duration timestamps, consecutive duplicates, overlapping time ranges) are dropped before writing the SRT.
3. **Export** — Valid segments are formatted as standard SRT with `HH:MM:SS,mmm` timestamps.

## Troubleshooting

| Issue                              | Fix                                                                            |
| ---------------------------------- | ------------------------------------------------------------------------------ |
| `ModuleNotFoundError: mlx_whisper` | Activate your venv and run `pip install mlx-whisper`                           |
| `Local file not found`             | Check the path, or use `-` as the first argument for stream mode               |
| Slow first run                     | The model is downloading (~3.1 GB); later runs use the cached copy             |
| Poor subtitle quality              | Try a different `language` code or switch between `transcribe` and `translate` |

## License

MIT (via mlx-whisper and the Whisper model weights; see upstream projects for details).

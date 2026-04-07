# WhisperX Transcriber

A desktop application for transcribing audio files with speaker identification, powered by [WhisperX](https://github.com/m-bain/whisperX). Supports 90+ languages with Korean as the default.

**[한국어](../ko-kr/README.md)**

---

## Features

- **Multi-language speech-to-text** using Whisper large-v3 (Korean default, 90+ languages supported)
- **Speaker diarization** — automatically identifies and labels different speakers
- **Word-level timestamps** for precise alignment
- **Export** transcripts in TXT, SRT (subtitles), or JSON
- **GPU acceleration** with automatic CPU fallback
- **Drag & drop** Electron UI with real-time progress

## Prerequisites

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** — Python package manager
- **Node.js 18+** and npm
- **FFmpeg** — for audio decoding (usually pre-installed on Linux)
- **(Optional) NVIDIA GPU** with CUDA — significantly faster than CPU

## Setup

### 1. Install Python dependencies

```bash
uv sync
```

### 2. Install Electron

```bash
cd electron
npm install
cd ..
```

### 3. Configure HuggingFace token (for speaker diarization)

Speaker diarization requires a HuggingFace token. You must first accept the model license:

- https://huggingface.co/pyannote/speaker-diarization-community-1

Then create a token at https://huggingface.co/settings/tokens (Read access) and add it to `.env`:

```bash
echo 'HF_TOKEN=hf_your_token_here' > .env
```

> Without a token, transcription still works — speaker labels will just be omitted.

## Usage

### Desktop App (Electron)

Start the API server and Electron app in two separate terminals:

```bash
# Terminal 1 — API server
uv run uvicorn api:app --reload

# Terminal 2 — Electron app
cd electron && npm start
```

1. Drop or select an audio file (MP3, WAV, M4A, FLAC, OGG, etc.)
2. Click **Transcribe**
3. View the transcript with speaker labels and timestamps
4. Export as TXT, SRT, or JSON

### Command Line

```bash
# Print transcript to terminal (Korean by default)
uv run python transcribe.py audio.mp3

# Specify a different language
uv run python transcribe.py audio.mp3 -l en

# Save to file
uv run python transcribe.py audio.mp3 -o transcript.txt

# Without speaker diarization
uv run python transcribe.py audio.mp3 --no-diarize
```

## Export Formats

| Format | Description | Use Case |
|--------|-------------|----------|
| **TXT** | Plain text with timestamps and speaker labels | Reading, sharing |
| **SRT** | SubRip subtitle format | Video players, subtitle editors |
| **JSON** | Structured data with start, end, text, speaker | Programmatic processing |

### TXT example

```
[0.0s - 3.2s] SPEAKER_00: 안녕하세요 오늘은 날씨가 좋습니다
[3.5s - 6.1s] SPEAKER_01: 네 정말 좋네요
```

### SRT example

```
1
00:00:00,000 --> 00:00:03,200
SPEAKER_00: 안녕하세요 오늘은 날씨가 좋습니다

2
00:00:03,500 --> 00:00:06,100
SPEAKER_01: 네 정말 좋네요
```

## Project Structure

```
ai_notes/
├── transcribe.py       # Core transcription logic
├── api.py              # FastAPI backend server
├── .env                # HuggingFace token (not committed)
├── electron/
│   ├── main.js         # Electron main process
│   ├── index.html      # UI
│   └── package.json
└── docs/
    ├── en-us/README.md
    └── ko-kr/README.md
```

## Troubleshooting

### CUDA out of memory

The Whisper large-v3 model needs ~8GB VRAM. If you see OOM errors:

1. Check for stale GPU processes: `nvidia-smi`
2. Kill them: `kill <PID>`
3. Restart the API server

### Electron sandbox error on Linux

If you see a SUID sandbox error, the app is already configured with `--no-sandbox` in `package.json`.

### Model download is slow

The first run downloads ~3GB for the Whisper model. This is a one-time download — subsequent runs load from cache.

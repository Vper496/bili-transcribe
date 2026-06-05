# bili-transcribe

[中文](README.md)

[![Stars](https://img.shields.io/github/stars/Vper496/bili-transcribe?style=social)](https://github.com/Vper496/bili-transcribe/stargazers)
[![License](https://img.shields.io/github/license/Vper496/bili-transcribe?style=flat-square&color=blue)](LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/Vper496/bili-transcribe?style=flat-square)](https://github.com/Vper496/bili-transcribe/commits/master)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Issues](https://img.shields.io/github/issues/Vper496/bili-transcribe?style=flat-square)](https://github.com/Vper496/bili-transcribe/issues)

Download Bilibili video audio and transcribe to markdown via faster-whisper. BV号 in, markdown out.

## Features

- **One BV number → markdown**: downloads audio via B站 API, transcribes with Whisper
- **CDN auto-fallback**: high-bitrate CDN nodes blocked in some regions → automatically tries lower bitrate streams
- **CPU-only**: faster-whisper small model + int8 quantization, no GPU needed (~500MB model, cached after first download)
- **~4.7x realtime**: 15 min video = ~3 min processing on modern CPU

## Prerequisites

- Python 3.10+
- ffmpeg (bundled via `imageio-ffmpeg`, no system install needed)

## Install

```bash
pip install -r requirements.txt
```

First run downloads the Whisper model (~500MB). If HuggingFace is blocked in your region:

```bash
# Windows (PowerShell)
$env:HF_ENDPOINT = "https://hf-mirror.com"

# Linux / macOS
export HF_ENDPOINT=https://hf-mirror.com
```

## Usage

```bash
# Step 1: Download audio (B站 API → WAV)
python download_audio.py BV1s4411C7hk

# Step 2: Transcribe (WAV → markdown + plain text)
python transcribe_audio.py \
  "scripts/transcripts/BV1s4411C7hk_audio.wav" \
  "Video Title" \
  "BV1s4411C7hk" \
  "935"
```

Output:
- `{bvid}.md` — markdown with frontmatter (title, source, author, duration)
- `{bvid}.txt` — plain text only

## How It Works

```
Video(bvid) → B站 API → DASH audio URL (sorted by bandwidth ASC)
                          ↓
                    try each quality level until one succeeds
                    (different bandwidth = different CDN)
                          ↓
                    download .m4s → convert to 16kHz mono WAV
                          ↓
                    faster-whisper small (zh, beam=5, VAD)
                          ↓
                    .md + .txt
```

## Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| `python: command not found` (Windows) | Windows App Installer redirector | Use full Python path |
| HuggingFace timeout | hf.co blocked in China | `export HF_ENDPOINT=https://hf-mirror.com` |
| 412 Precondition Failed | B站 API WBI signing | `bilibili-api-python` handles it automatically |
| CDN timeout (`mcdn.bilivideo.cn`) | High-quality stream uses blocked CDN | Script auto-falls back to lower bitrate |
| No CC subtitles | Video has no uploaded subtitles | ASR (faster-whisper) is the fallback |

## Notes

- Audio is downloaded at the lowest available bitrate (43-46kbps) which is sufficient for Whisper and has the best CDN routing
- WAV files are cleaned up after transcription
- The `small` Whisper model is downloaded once and cached locally

## Star History

[![Star History](https://api.star-history.com/svg?repos=Vper496/bili-transcribe&type=Date)](https://star-history.com/#Vper496/bili-transcribe&Date)

## License

MIT

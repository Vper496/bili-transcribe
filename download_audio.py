"""Download audio from B站 video and convert to WAV for Whisper."""
import os
import sys
import subprocess
import requests
from pathlib import Path
from bilibili_api import video, sync
import imageio_ffmpeg


def main(bvid: str):
    # Step 1: Get video info and audio URL
    print("=" * 60)
    print("Step 1: getting video info and audio stream...")

    v = video.Video(bvid=bvid)
    info = sync(v.get_info())
    title = info["title"].replace("/", "_").replace("\\", "_")
    duration = info["duration"]
    print(f"  Title: {title}")
    print(f"  Duration: {duration} seconds ({duration // 60}:{duration % 60:02d})")

    url_data = sync(v.get_download_url(cid=info["cid"]))
    audio_list = url_data["dash"]["audio"]
    # Sort by bandwidth ascending — low quality uses more reliable CDNs
    audio_list = sorted(audio_list, key=lambda x: x.get("bandwidth", 0))

    # Step 2: Download audio (try all quality levels, CDN varies per quality)
    print("Step 2: downloading audio...")
    work_dir = Path(__file__).resolve().parent / "transcripts"
    work_dir.mkdir(parents=True, exist_ok=True)

    audio_m4s = work_dir / f"{bvid}_audio.m4s"
    audio_wav = work_dir / f"{bvid}_audio.wav"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        ),
        "Referer": "https://www.bilibili.com/",
    }

    downloaded = False
    for a in audio_list:
        url = a.get("base_url", a.get("baseUrl", ""))
        host = url.split("/")[2] if "://" in url else "unknown"
        bw = a.get("bandwidth", 0) // 1000
        print(f"  trying {bw}kbps from {host}...")
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            audio_m4s.write_bytes(resp.content)
            size_mb = len(resp.content) / 1024 / 1024
            print(f"  downloaded: {size_mb:.1f} MB")
            downloaded = True
            break
        except Exception as e:
            print(f"  failed: {e}")
            continue

    if not downloaded:
        print("  ERROR: all audio streams failed")
        sys.exit(1)

    # Step 3: Convert to WAV (16kHz mono for Whisper)
    print("Step 3: converting to WAV...")
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    print(f"  ffmpeg: {ffmpeg_exe}")

    cmd = [
        ffmpeg_exe, "-y",
        "-i", str(audio_m4s),
        "-ac", "1",
        "-ar", "16000",
        "-f", "wav",
        str(audio_wav),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        wav_size = audio_wav.stat().st_size / 1024 / 1024
        print(f"  converted: {wav_size:.1f} MB WAV")
    else:
        print(f"  ffmpeg error: {result.stderr[:800]}")
        sys.exit(1)

    # Clean up m4s
    audio_m4s.unlink()

    print(f"\nAudio ready: {audio_wav}")
    print(f"Duration: {duration} seconds")
    return {
        "bvid": bvid,
        "title": title,
        "duration": duration,
        "wav_path": str(audio_wav),
    }


if __name__ == "__main__":
    bvid = sys.argv[1] if len(sys.argv) > 1 else "BV1s4411C7hk"
    result = main(bvid)
    print(f"\nRESULT: {result}")

"""Transcribe audio to text using faster-whisper and output as markdown."""
import sys
import json
import time
from pathlib import Path


def format_timestamp(seconds: float) -> str:
    """Convert seconds to MM:SS format."""
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"


def transcribe(wav_path: str, title: str, bvid: str, duration: int):
    import os
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
    from faster_whisper import WhisperModel

    print(f"Loading Whisper model (small)...")
    # Use small model, CPU, int8 quantization for speed
    model = WhisperModel("small", device="cpu", compute_type="int8")

    print(f"Transcribing: {title}")
    print(f"Duration: {duration // 60}:{duration % 60:02d}")
    print()

    start_time = time.time()
    segments, info = model.transcribe(
        wav_path,
        language="zh",
        beam_size=5,
        vad_filter=True,       # filter out silence
        vad_parameters=dict(
            min_silence_duration_ms=500,
        ),
    )

    print(f"Detected language: {info.language} (probability: {info.language_probability:.2f})")
    print(f"Duration after VAD: {info.duration_after_vad:.0f} seconds")
    print()

    # Collect segments
    all_segments = []
    print("Transcribing...")
    for seg in segments:
        all_segments.append({
            "start": seg.start,
            "end": seg.end,
            "text": seg.text.strip(),
        })
        # Progress indicator
        elapsed = time.time() - start_time
        progress = seg.end / duration * 100
        speed = seg.end / elapsed if elapsed > 0 else 0
        print(f"\r  [{format_timestamp(seg.end)} / {format_timestamp(duration)}] "
              f"{progress:.0f}% @ {speed:.1f}x realtime", end="", flush=True)

    elapsed = time.time() - start_time
    print(f"\n\nTranscription complete in {elapsed:.0f}s ({elapsed / duration:.1f}x realtime)")

    # Generate markdown output
    out_dir = Path(wav_path).parent
    md_path = out_dir / f"{bvid}.md"
    txt_path = out_dir / f"{bvid}.txt"

    # Plain text (no timestamps)
    full_text = "\n".join(seg["text"] for seg in all_segments)
    txt_path.write_text(full_text, encoding="utf-8")

    # Markdown with metadata and optional timestamps
    md_lines = [
        "---",
        f"title: {title}",
        f"source: https://www.bilibili.com/video/{bvid}",
        f"author: 达奇上校",
        f"duration: {duration}",
        f"transcribed: true",
        "---",
        "",
        f"# {title}",
        "",
        f"> 来源: [B站视频](https://www.bilibili.com/video/{bvid})",
        f"> UP主: 达奇上校",
        f"> 时长: {duration // 60}:{duration % 60:02d}",
        f"> 转写模型: faster-whisper small",
        "",
        "---",
        "",
    ]

    # Add text with optional timestamps (every ~30 seconds for navigation)
    for seg in all_segments:
        # Add timestamp marker every ~30 seconds
        if seg["start"] % 30 < 5:  # first segment in each 30s window
            md_lines.append(f"\n<!-- t={format_timestamp(seg['start'])} -->\n")
        md_lines.append(seg["text"])

    md_text = "\n".join(md_lines)
    md_path.write_text(md_text, encoding="utf-8")

    print(f"\nOutput files:")
    print(f"  Markdown: {md_path} ({len(md_text)} chars)")
    print(f"  Plain text: {txt_path} ({len(full_text)} chars)")

    return {
        "bvid": bvid,
        "title": title,
        "duration": duration,
        "segments": len(all_segments),
        "text_length": len(full_text),
        "md_path": str(md_path),
        "txt_path": str(txt_path),
    }


if __name__ == "__main__":
    wav_path = sys.argv[1] if len(sys.argv) > 1 else "scripts/transcripts/BV1s4411C7hk_audio.wav"
    title = sys.argv[2] if len(sys.argv) > 2 else "让人类再次伟大！帝皇的崛起！"
    bvid = sys.argv[3] if len(sys.argv) > 3 else "BV1s4411C7hk"
    duration = int(sys.argv[4]) if len(sys.argv) > 4 else 935

    result = transcribe(wav_path, title, bvid, duration)
    print(f"\nRESULT: {json.dumps(result, ensure_ascii=False)}")

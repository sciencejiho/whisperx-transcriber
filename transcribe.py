import argparse
import json
import os
import sys
from pathlib import Path

import torch
import whisperx
from whisperx.diarize import DiarizationPipeline


def get_device() -> tuple[str, str]:
    if torch.cuda.is_available():
        return "cuda", "float16"
    return "cpu", "int8"


def transcribe(
    audio_path: str,
    output_path: str | None = None,
    progress_callback=None,
    diarize: bool = True,
    language: str = "ko",
) -> list[dict]:
    device, compute_type = get_device()
    batch_size = 16 if device == "cuda" else 4

    if progress_callback:
        progress_callback("loading_model", "Loading WhisperX model...")

    # 1. Load and transcribe audio
    model = whisperx.load_model(
        "large-v3", device, compute_type=compute_type, language=language
    )
    audio = whisperx.load_audio(audio_path)

    if progress_callback:
        progress_callback("transcribing", "Transcribing audio...")

    result = model.transcribe(audio, batch_size=batch_size, language=language)

    if progress_callback:
        progress_callback("aligning", "Aligning timestamps...")

    # 2. Align whisper output for word-level timestamps
    align_model, metadata = whisperx.load_align_model(
        language_code=language, device=device
    )
    result = whisperx.align(
        result["segments"],
        align_model,
        metadata,
        audio,
        device,
        return_char_alignments=False,
    )

    # 3. Speaker diarization
    hf_token = os.environ.get("HF_TOKEN")
    if diarize and hf_token:
        if progress_callback:
            progress_callback("diarizing", "Identifying speakers...")

        diarize_model = DiarizationPipeline(token=hf_token, device=device)
        diarize_segments = diarize_model(audio)
        result = whisperx.assign_word_speakers(diarize_segments, result)
    elif diarize and not hf_token:
        if progress_callback:
            progress_callback("diarizing", "Skipping diarization (no HF_TOKEN set)")

    # 4. Build structured segments
    segments = []
    for seg in result["segments"]:
        segments.append(
            {
                "start": round(seg["start"], 1),
                "end": round(seg["end"], 1),
                "text": seg["text"].strip(),
                "speaker": seg.get("speaker", None),
            }
        )

    # 5. Write to file or stdout
    if output_path:
        Path(output_path).write_text(format_txt(segments), encoding="utf-8")
        print(f"Saved transcript to {output_path}")
    else:
        print(format_txt(segments))

    return segments


def format_txt(segments: list[dict]) -> str:
    lines = []
    for seg in segments:
        speaker = f"{seg['speaker']}: " if seg.get("speaker") else ""
        lines.append(
            f"[{seg['start']:.1f}s - {seg['end']:.1f}s] {speaker}{seg['text']}"
        )
    return "\n".join(lines)


def format_srt(segments: list[dict]) -> str:
    lines = []
    for i, seg in enumerate(segments, 1):
        start = _srt_time(seg["start"])
        end = _srt_time(seg["end"])
        speaker = f"{seg['speaker']}: " if seg.get("speaker") else ""
        lines.append(f"{i}\n{start} --> {end}\n{speaker}{seg['text']}\n")
    return "\n".join(lines)


def _srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def format_json(segments: list[dict]) -> str:
    return json.dumps(segments, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Transcribe audio using WhisperX")
    parser.add_argument("audio", help="Path to audio file")
    parser.add_argument(
        "-o", "--output", help="Output text file path (default: print to stdout)"
    )
    parser.add_argument(
        "-l", "--language", default="ko", help="Language code (default: ko)"
    )
    parser.add_argument(
        "--no-diarize", action="store_true", help="Disable speaker diarization"
    )
    args = parser.parse_args()

    if not Path(args.audio).exists():
        print(f"Error: file not found: {args.audio}", file=sys.stderr)
        sys.exit(1)

    transcribe(
        args.audio, args.output, diarize=not args.no_diarize, language=args.language
    )


if __name__ == "__main__":
    main()

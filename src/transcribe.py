"""音声書き起こし（OpenAI Whisper）"""

import json
from pathlib import Path

import typer
from openai import OpenAI


def transcribe(
    video_path: Path,
    output_dir: Path = Path("cache/transcripts"),
) -> None:
    """音声書き起こし（OpenAI Whisper）"""
    client = OpenAI()
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(video_path, "rb") as f:
        result = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="verbose_json",
            timestamp_granularities=["segment"],
        )
    out_path = output_dir / f"{video_path.stem}.json"
    out_path.write_text(
        json.dumps(result.model_dump(), ensure_ascii=False, indent=2)
    )
    typer.echo(f"✅ 書き起こし完了: {out_path}")

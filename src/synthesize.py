"""音声合成（OpenAI TTS）"""

import json
from pathlib import Path

import typer
from openai import OpenAI


def synthesize(
    transcript_path: Path,
    output_dir: Path = Path("cache/audio"),
    voice: str = typer.Option(
        "nova", help="音声: alloy/echo/fable/onyx/nova/shimmer/coral/sage 等"
    ),
    model: str = typer.Option(
        "gpt-4o-mini-tts", help="TTSモデル (gpt-4o-mini-tts / tts-1 / tts-1-hd)"
    ),
    response_format: str = typer.Option(
        "mp3", help="出力形式: mp3 / opus / aac / flac / wav"
    ),
    speed: float = typer.Option(1.0, help="再生速度 (0.25〜4.0)"),
    instructions: str = typer.Option(
        "", "--instructions", help="話し方の指示（gpt-4o-mini-tts のみ）"
    ),
    by_segment: bool = typer.Option(
        False, "--by-segment", help="セグメント毎に分割して音声生成"
    ),
) -> None:
    """書き起こしテキストを音声合成（OpenAI TTS）"""
    transcript = json.loads(transcript_path.read_text())
    text = transcript.get("text", "")
    segments = transcript.get("segments", [])
    if not text:
        typer.echo("❌ 書き起こしテキストが空", err=True)
        raise typer.Exit(1)

    client = OpenAI()
    audio_dir = output_dir / transcript_path.stem
    audio_dir.mkdir(parents=True, exist_ok=True)

    def _create(input_text: str, out_path: Path) -> None:
        kwargs: dict = {
            "model": model,
            "voice": voice,
            "input": input_text,
            "response_format": response_format,
            "speed": speed,
        }
        if instructions:
            kwargs["instructions"] = instructions
        with client.audio.speech.with_streaming_response.create(**kwargs) as r:
            r.stream_to_file(out_path)

    if by_segment:
        if not segments:
            typer.echo("❌ segments が無いので --by-segment 不可", err=True)
            raise typer.Exit(1)
        typer.echo(
            f"🎤 セグメント毎に音声合成中（{model}, {voice}, {len(segments)}本）..."
        )
        for i, seg in enumerate(segments):
            seg_text = seg.get("text", "").strip()
            if not seg_text:
                continue
            out_path = audio_dir / f"segment_{i:03d}.{response_format}"
            _create(seg_text, out_path)
        typer.echo(f"✅ セグメント音声合成完了: {audio_dir}")
    else:
        typer.echo(f"🎤 音声合成中（{model}, {voice}）...")
        out_path = audio_dir / f"voiceover.{response_format}"
        _create(text, out_path)
        typer.echo(f"✅ 音声合成完了: {out_path}")

    meta = {
        "voice": voice,
        "model": model,
        "speed": speed,
        "instructions": instructions,
        "by_segment": by_segment,
        "text": text,
        "source_transcript": str(transcript_path),
    }
    (audio_dir / "voiceover.meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2)
    )

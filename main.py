"""video-clone: 参考動画クローン生成システム"""

import json
from pathlib import Path

import typer
import yt_dlp
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = typer.Typer(help="参考動画クローン生成システム", no_args_is_help=True)


@app.command()
def download(
    url: str,
    output_dir: Path = Path("cache/videos"),
) -> None:
    """参考動画をダウンロード（yt-dlp）"""
    output_dir.mkdir(parents=True, exist_ok=True)
    ydl_opts = {
        "format": "best[ext=mp4]/best",
        "outtmpl": str(output_dir / "%(id)s.%(ext)s"),
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        path = Path(ydl.prepare_filename(info))
    typer.echo(f"✅ ダウンロード完了: {path}")


@app.command()
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


if __name__ == "__main__":
    app()

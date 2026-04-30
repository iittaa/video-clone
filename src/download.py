"""動画ダウンロード（yt-dlp）"""

from pathlib import Path

import typer
import yt_dlp


def download(
    url: str,
    output_dir: Path = Path("cache/videos"),
) -> Path:
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
    return path

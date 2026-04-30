"""動画クリップ生成（fal.ai Seedance 1 Pro）"""

import json
import urllib.request
from pathlib import Path

import fal_client
import typer


def generate_clip(
    analysis_path: Path,
    image_path: Path = typer.Option(
        None, "--image", help="ベース画像（省略時 cache/images/<stem>/character.png）"
    ),
    frame_index: int = typer.Option(0, "--index", "-i", help="cuts配列のインデックス"),
    duration: int = typer.Option(5, help="動画の長さ（2〜12秒）"),
    aspect_ratio: str = typer.Option("9:16", help="アスペクト比"),
    resolution: str = typer.Option("1080p", help="解像度（480p/720p/1080p）"),
    camera_fixed: bool = typer.Option(False, help="カメラを固定"),
    output_dir: Path = Path("cache/clips"),
    model: str = typer.Option(
        "fal-ai/bytedance/seedance/v1/pro/image-to-video",
        help="fal.ai モデルID",
    ),
) -> None:
    """1カット分の動画を生成（fal.ai Seedance 1 Pro）"""
    analysis = json.loads(analysis_path.read_text())
    cuts = analysis.get("cuts", [])
    if frame_index >= len(cuts):
        typer.echo(
            f"❌ frame_index {frame_index} は範囲外（cuts数: {len(cuts)}）", err=True
        )
        raise typer.Exit(1)

    cut = cuts[frame_index]
    description = cut.get("description", "")
    character = analysis.get("character", {})

    if image_path is None:
        image_path = Path("cache/images") / analysis_path.stem / "character.png"
    if not image_path.exists():
        typer.echo(f"❌ 画像が見つからない: {image_path}", err=True)
        raise typer.Exit(1)

    prompt = (
        f"{description}\n\n"
        f"人物: {character.get('age_range', '')}{character.get('gender', '')}, "
        f"{character.get('outfit', '')}\n"
        f"雰囲気: {analysis.get('atmosphere', '')}\n"
        f"撮影: {analysis.get('filming_style', '')}"
    )

    typer.echo("📤 画像をfal.aiにアップロード中...")
    image_url = fal_client.upload_file(str(image_path))

    typer.echo(f"🎬 動画生成中（カット {frame_index}, {duration}秒, {resolution}）...")
    arguments = {
        "prompt": prompt,
        "image_url": image_url,
        "duration": duration,
        "aspect_ratio": aspect_ratio,
        "resolution": resolution,
        "camera_fixed": camera_fixed,
    }
    result = fal_client.subscribe(model, arguments=arguments, with_logs=False)

    video_url = result["video"]["url"]
    out_dir = output_dir / analysis_path.stem
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{frame_index:03d}.mp4"
    urllib.request.urlretrieve(video_url, out_path)

    meta = {
        "prompt": prompt,
        "model": model,
        "arguments": {**arguments, "image_url": str(image_path)},
        "source_analysis": str(analysis_path),
        "frame_index": frame_index,
        "cut": cut,
        "video_url": video_url,
        "seed": result.get("seed"),
    }
    (out_dir / f"{frame_index:03d}.meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2)
    )
    typer.echo(f"✅ 動画クリップ生成完了: {out_path}")

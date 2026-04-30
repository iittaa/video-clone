"""キャラ画像生成（GPT Image）"""

import base64
import json
from pathlib import Path

import typer
from openai import OpenAI


def generate_character(
    analysis_path: Path,
    output_dir: Path = Path("cache/images"),
    model: str = typer.Option("gpt-image-1", help="画像生成モデル"),
    size: str = typer.Option("1024x1536", help="画像サイズ（9:16縦型は1024x1536）"),
    quality: str = typer.Option("medium", help="品質: low / medium / high"),
) -> None:
    """解析結果からキャラ画像を生成（GPT Image）"""
    analysis = json.loads(analysis_path.read_text())
    character = analysis.get("character", {})
    atmosphere = analysis.get("atmosphere", "")
    color_palette = analysis.get("color_palette", "")
    filming_style = analysis.get("filming_style", "")

    prompt = f"""縦型ショート動画用のキャラクター人物写真。

人物属性:
- 年齢: {character.get("age_range", "20代")}
- 性別: {character.get("gender", "")}
- 外見: {character.get("appearance", "")}
- 服装: {character.get("outfit", "")}

撮影条件:
- 雰囲気: {atmosphere}
- 色味: {color_palette}
- スタイル: {filming_style}

要件:
- 9:16 縦型構図、人物を中央に配置
- 自然光のリアルな写真風（実写、CG感なし）
- 表情はニュートラルで動画化しやすい正面寄り
- 背景は雰囲気に合わせるが人物より目立たせない
- 顔は鮮明、後で他カット用に流用するためアイデンティティを強く出す
"""

    client = OpenAI()
    output_dir.mkdir(parents=True, exist_ok=True)
    image_dir = output_dir / analysis_path.stem
    image_dir.mkdir(parents=True, exist_ok=True)

    typer.echo(f"🎨 キャラ画像生成中（{model}, {quality}, {size}）...")
    response = client.images.generate(
        model=model,
        prompt=prompt,
        size=size,
        quality=quality,
        n=1,
    )

    image_data = base64.b64decode(response.data[0].b64_json)
    out_path = image_dir / "character.png"
    out_path.write_bytes(image_data)

    meta = {
        "prompt": prompt,
        "model": model,
        "size": size,
        "quality": quality,
        "source_analysis": str(analysis_path),
        "usage": response.usage.model_dump() if response.usage else None,
    }
    (image_dir / "character.meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2)
    )

    typer.echo(f"✅ キャラ画像生成完了: {out_path}")

"""video-clone: 参考動画クローン生成システム"""

import base64
import json
import re
import subprocess
import urllib.request
from pathlib import Path

import fal_client
import typer
import yt_dlp
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)

app = typer.Typer(help="参考動画クローン生成システム", no_args_is_help=True)


def _get_video_duration(video_path: Path) -> float:
    """ffmpeg の stderr から動画長（秒）を抽出"""
    result = subprocess.run(
        ["ffmpeg", "-i", str(video_path)],
        capture_output=True,
        text=True,
    )
    match = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", result.stderr)
    if not match:
        raise RuntimeError(f"動画長を取得できませんでした: {video_path}")
    h, m, s = match.groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


def _extract_frame(video_path: Path, timestamp: float, output_path: Path) -> None:
    """指定秒数のフレームを1枚抽出"""
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            str(timestamp),
            "-i",
            str(video_path),
            "-frames:v",
            "1",
            "-q:v",
            "3",
            str(output_path),
        ],
        check=True,
        capture_output=True,
    )


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


@app.command()
def analyze(
    video_path: Path,
    transcript_path: Path = typer.Option(
        None, "--transcript", "-t", help="書き起こしJSON（省略可）"
    ),
    frames: int = typer.Option(10, "--frames", "-n", help="サンプリングするフレーム数"),
    model: str = typer.Option("gpt-4o", help="使用するVisionモデル"),
    detail: str = typer.Option("low", help="画像詳細度（low / high）"),
    output_dir: Path = Path("cache/analysis"),
    frames_dir: Path = Path("cache/frames"),
) -> None:
    """動画構成をVision APIで解析（GPT-4o low detail デフォルト）"""
    output_dir.mkdir(parents=True, exist_ok=True)
    video_stem = video_path.stem
    frame_dir = frames_dir / video_stem
    frame_dir.mkdir(parents=True, exist_ok=True)

    duration = _get_video_duration(video_path)
    interval = duration / frames

    typer.echo(f"📐 動画長: {duration:.1f}秒、{frames}フレーム抽出中...")
    frame_paths: list[Path] = []
    for i in range(frames):
        t = interval * i + interval / 2
        out = frame_dir / f"{i:03d}.jpg"
        _extract_frame(video_path, t, out)
        frame_paths.append(out)

    transcript_text = ""
    if transcript_path and transcript_path.exists():
        transcript = json.loads(transcript_path.read_text())
        segments = transcript.get("segments", [])
        transcript_text = "\n".join(
            f"[{s['start']:.1f}-{s['end']:.1f}] {s['text']}" for s in segments
        )

    images = []
    for fp in frame_paths:
        b64 = base64.b64encode(fp.read_bytes()).decode()
        images.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{b64}",
                    "detail": detail,
                },
            }
        )

    prompt = f"""あなたは動画クローン生成システムの解析担当です。
以下は参考動画から均等にサンプリングした{frames}枚のフレームです（順番にframe_index 0〜{frames - 1}）。
動画長: {duration:.1f}秒

書き起こしテキスト（タイムスタンプ付き、空の場合は音声なし）:
{transcript_text or "(なし)"}

これらの情報をもとに、動画の構成を以下のJSON形式で必ず出力してください。
日本語で記述してください。

**重要：cuts 配列には必ず {frames} 個の要素を含めてください（frame_index 0 から {frames - 1} まで全フレーム分）。省略禁止。**
**テロップは画面上に表示されている文字を一文字単位で正確に書き写してください。文字がなければ空文字。**

{{
  "scene_summary": "動画全体の概要（1〜2文）",
  "atmosphere": "雰囲気・トーン（カジュアル/シリアス/コミカル等）",
  "color_palette": "色味の傾向（暖色/寒色/モノトーン等の説明）",
  "filming_style": "撮影スタイル（俯瞰/正面/手持ち感/固定カメラ等）",
  "character": {{
    "age_range": "推定年齢層",
    "gender": "性別",
    "appearance": "外見的特徴",
    "outfit": "服装"
  }},
  "cuts": [
    {{
      "frame_index": 0,
      "description": "このフレームで起きていること（人物の姿勢・動作・配置）",
      "telop_text": "画面に表示されているテロップ（なければ空文字）",
      "telop_style": "テロップのスタイル（位置・色・フォント感、なければ空文字）"
    }}
    // ... frame_index = {frames - 1} まで全{frames}個
  ]
}}
"""

    client = OpenAI()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}, *images],
            }
        ],
        response_format={"type": "json_object"},
    )

    result = json.loads(response.choices[0].message.content)
    result["_meta"] = {
        "video_path": str(video_path),
        "duration_sec": duration,
        "frame_count": frames,
        "model": model,
        "detail": detail,
        "usage": response.usage.model_dump() if response.usage else None,
    }

    out_path = output_dir / f"{video_stem}.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    typer.echo(f"✅ 解析完了: {out_path}")


@app.command("generate-character")
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


@app.command("generate-clip")
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


@app.command()
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


if __name__ == "__main__":
    app()

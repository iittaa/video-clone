"""URL一発で全工程実行する統合コマンド"""

import json
from pathlib import Path

import typer

from src.analyze import analyze
from src.compose import compose
from src.download import download
from src.generate_character import generate_character
from src.generate_clip import generate_clip
from src.synthesize import synthesize
from src.transcribe import transcribe


def clone(
    url: str,
    frames: int = typer.Option(10, "--frames", "-n", help="解析フレーム数 = カット数"),
    voice: str = typer.Option("nova", help="TTS音声"),
    character_quality: str = typer.Option("medium", help="キャラ画像の品質: low/medium/high"),
    clip_duration: int = typer.Option(5, help="各クリップの長さ（秒）"),
    clip_resolution: str = typer.Option("1080p", help="クリップ解像度: 480p/720p/1080p"),
    skip_clips: bool = typer.Option(False, "--skip-clips", help="動画クリップ生成をスキップ"),
    skip_compose: bool = typer.Option(False, "--skip-compose", help="最終合成をスキップ"),
) -> None:
    """URLを入れるだけで全工程実行（download→transcribe→analyze→character→clip×N→tts→compose）"""
    typer.echo(f"🚀 クローン開始: {url}")

    typer.echo("\n=== Step 1/7: ダウンロード ===")
    video_path = download(url=url, output_dir=Path("cache/videos"))
    stem = video_path.stem

    typer.echo("\n=== Step 2/7: 書き起こし ===")
    transcribe(video_path=video_path, output_dir=Path("cache/transcripts"))
    transcript_path = Path("cache/transcripts") / f"{stem}.json"

    typer.echo("\n=== Step 3/7: 構成解析 ===")
    analyze(
        video_path=video_path,
        transcript_path=transcript_path,
        frames=frames,
        model="gpt-4o",
        detail="low",
        output_dir=Path("cache/analysis"),
        frames_dir=Path("cache/frames"),
    )
    analysis_path = Path("cache/analysis") / f"{stem}.json"

    typer.echo("\n=== Step 4/7: キャラ画像生成 ===")
    generate_character(
        analysis_path=analysis_path,
        output_dir=Path("cache/images"),
        model="gpt-image-1",
        size="1024x1536",
        quality=character_quality,
    )

    if skip_clips:
        typer.echo("\n=== Step 5/7: クリップ生成（スキップ） ===")
    else:
        analysis = json.loads(analysis_path.read_text())
        cuts = analysis.get("cuts", [])
        typer.echo(f"\n=== Step 5/7: クリップ生成 × {len(cuts)} ===")
        success = 0
        failed: list[int] = []
        for i in range(len(cuts)):
            try:
                generate_clip(
                    analysis_path=analysis_path,
                    image_path=None,
                    frame_index=i,
                    duration=clip_duration,
                    aspect_ratio="9:16",
                    resolution=clip_resolution,
                    camera_fixed=False,
                    output_dir=Path("cache/clips"),
                    model="fal-ai/bytedance/seedance/v1/pro/image-to-video",
                )
                success += 1
            except Exception as e:
                typer.echo(f"⚠️  カット{i}失敗: {e}", err=True)
                failed.append(i)
        typer.echo(
            f"📊 クリップ生成結果: 成功 {success}/{len(cuts)}"
            + (f"、失敗インデックス {failed}" if failed else "")
        )

    typer.echo("\n=== Step 6/7: 音声合成 ===")
    synthesize(
        transcript_path=transcript_path,
        output_dir=Path("cache/audio"),
        voice=voice,
        model="gpt-4o-mini-tts",
        response_format="mp3",
        speed=1.0,
        instructions="",
        by_segment=False,
    )

    if skip_compose:
        typer.echo("\n=== Step 7/7: 最終合成（スキップ） ===")
        typer.echo(f"\n🎉 中間生成物まで完了: stem={stem}")
        return

    typer.echo("\n=== Step 7/7: 最終合成 ===")
    compose(
        analysis_path=analysis_path,
        output_dir=Path("output"),
        composition_root=Path("cache/compositions"),
        clips_dir=Path("cache/clips"),
        audio_dir=Path("cache/audio"),
        width=1080,
        height=1920,
        cut_duration=float(clip_duration),
        overlap=0.3,
        skip_render=False,
    )

    typer.echo(f"\n🎉 クローン完了: output/{stem}.mp4")

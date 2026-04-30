"""HyperFrames合成（カット動画 + テロップ + 音声 → 最終MP4）"""

import json
import shutil
import subprocess
from pathlib import Path

import typer


def _build_composition_html(
    cuts: list[dict],
    available_indices: list[int],
    has_audio: bool,
    width: int,
    height: int,
    cut_duration: float,
    overlap: float,
    title: str,
) -> tuple[str, float]:
    """HyperFrames composition の index.html を組み立て、(html, total_duration) を返す。"""
    step = cut_duration - overlap
    total_duration = step * (len(available_indices) - 1) + cut_duration if available_indices else 0

    video_html_parts: list[str] = []
    telop_html_parts: list[str] = []
    timeline_tweens: list[str] = []

    for slot, frame_index in enumerate(available_indices):
        start = round(slot * step, 3)
        track_index = slot % 2  # 隣接クリップを別トラックにしてオーバーラップ可能に
        video_html_parts.append(
            f'  <video id="v{frame_index}" class="cut-video" '
            f'data-start="{start}" data-duration="{cut_duration}" '
            f'data-track-index="{track_index}" '
            f'src="media/clip_{frame_index:03d}.mp4" muted playsinline></video>'
        )
        if overlap > 0 and slot > 0:
            timeline_tweens.append(
                f'  tl.from("#v{frame_index}", '
                f'{{ opacity: 0, duration: {overlap}, ease: "power1.inOut" }}, {start});'
            )

        cut = cuts[frame_index]
        telop = (cut.get("telop_text") or "").strip()
        if telop:
            telop_html = telop.replace("\n", "<br>")
            telop_start = round(start + 0.2, 3)
            telop_duration = round(cut_duration - 0.2, 3)
            telop_html_parts.append(
                f'  <div id="t{frame_index}" class="telop" '
                f'data-start="{telop_start}" data-duration="{telop_duration}" '
                f'data-track-index="2"><div class="telop-text">{telop_html}</div></div>'
            )
            timeline_tweens.append(
                f'  tl.from("#t{frame_index} .telop-text", '
                f'{{ y: 30, opacity: 0, duration: 0.4, ease: "power3.out" }}, {telop_start});'
            )

    audio_html = ""
    if has_audio:
        audio_html = (
            f'  <audio id="voice" data-start="0" data-duration="{total_duration}" '
            f'data-track-index="3" src="media/voiceover.mp3" data-volume="1.0"></audio>'
        )

    timeline_js = "\n".join(timeline_tweens) or "  // (no tweens)"
    video_html = "\n".join(video_html_parts)
    telop_html = "\n".join(telop_html_parts)

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>{title}</title>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
</head>
<body>
<div data-composition-id="root" data-width="{width}" data-height="{height}" data-duration="{total_duration}">
  <style>
    [data-composition-id="root"] {{
      position: relative;
      background: #000;
      width: 100%;
      height: 100%;
      overflow: hidden;
      font-family: "Hiragino Sans", "Yu Gothic", "Helvetica Neue", sans-serif;
    }}
    [data-composition-id="root"] .cut-video {{
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      object-fit: cover;
    }}
    [data-composition-id="root"] .telop {{
      position: absolute;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      pointer-events: none;
      padding: 0 80px;
    }}
    [data-composition-id="root"] .telop-text {{
      color: #fff;
      font-size: 80px;
      font-weight: 900;
      text-align: center;
      line-height: 1.25;
      max-width: 100%;
      text-shadow:
        4px 4px 0 #000, -4px -4px 0 #000,
        4px -4px 0 #000, -4px 4px 0 #000,
        4px 0 0 #000, -4px 0 0 #000,
        0 4px 0 #000, 0 -4px 0 #000;
    }}
  </style>
{video_html}
{telop_html}
{audio_html}
  <script>
    window.__timelines = window.__timelines || {{}};
    const tl = gsap.timeline({{ paused: true }});
{timeline_js}
    window.__timelines["root"] = tl;
  </script>
</div>
</body>
</html>
"""
    return html, total_duration


def compose(
    analysis_path: Path,
    output_dir: Path = Path("output"),
    composition_root: Path = Path("cache/compositions"),
    clips_dir: Path = Path("cache/clips"),
    audio_dir: Path = Path("cache/audio"),
    width: int = typer.Option(1080, help="出力幅（縦型 9:16 想定）"),
    height: int = typer.Option(1920, help="出力高さ"),
    cut_duration: float = typer.Option(5.0, help="各カットの長さ（秒）"),
    overlap: float = typer.Option(0.3, help="カット間のクロスフェード時間（秒）"),
    skip_render: bool = typer.Option(
        False, "--skip-render", help="HTML生成のみで render を行わない"
    ),
) -> None:
    """各カット動画 + 音声 + テロップを HyperFrames で合成して最終MP4を生成"""
    analysis = json.loads(analysis_path.read_text())
    cuts = analysis.get("cuts", [])
    if not cuts:
        typer.echo("❌ analysis JSON に cuts が無い", err=True)
        raise typer.Exit(1)

    stem = analysis_path.stem
    proj_dir = composition_root / stem
    media_dir = proj_dir / "media"
    media_dir.mkdir(parents=True, exist_ok=True)

    clips_src = clips_dir / stem
    audio_src = audio_dir / stem / "voiceover.mp3"

    available_indices: list[int] = []
    for i in range(len(cuts)):
        src = clips_src / f"{i:03d}.mp4"
        if src.exists():
            shutil.copy(src, media_dir / f"clip_{i:03d}.mp4")
            available_indices.append(i)

    if not available_indices:
        typer.echo(
            f"❌ {clips_src} に動画クリップが無い。先に generate-clip を全カット実行する必要がある",
            err=True,
        )
        raise typer.Exit(1)

    has_audio = audio_src.exists()
    if has_audio:
        shutil.copy(audio_src, media_dir / "voiceover.mp3")

    html, total_duration = _build_composition_html(
        cuts=cuts,
        available_indices=available_indices,
        has_audio=has_audio,
        width=width,
        height=height,
        cut_duration=cut_duration,
        overlap=overlap,
        title=stem,
    )
    (proj_dir / "index.html").write_text(html, encoding="utf-8")

    hf_config = {"name": stem, "width": width, "height": height}
    (proj_dir / "hyperframes.json").write_text(
        json.dumps(hf_config, ensure_ascii=False, indent=2)
    )

    typer.echo(
        f"📝 composition 生成: {proj_dir / 'index.html'}（{len(available_indices)}カット, "
        f"{total_duration:.1f}秒, audio={'有' if has_audio else '無'}）"
    )

    if skip_render:
        typer.echo("⏭  --skip-render が指定されたためレンダリングをスキップ")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{stem}.mp4"
    typer.echo("🎞️  HyperFrames でレンダリング中...")
    subprocess.run(
        ["npx", "hyperframes", "render", "-o", str(out_path.resolve())],
        cwd=proj_dir,
        check=True,
    )
    typer.echo(f"✅ 動画合成完了: {out_path}")

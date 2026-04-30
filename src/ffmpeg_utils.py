"""ffmpeg を使った動画処理ヘルパー"""

import re
import subprocess
from pathlib import Path


def get_video_duration(video_path: Path) -> float:
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


def extract_frame(video_path: Path, timestamp: float, output_path: Path) -> None:
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

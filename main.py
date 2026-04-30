"""video-clone: 参考動画クローン生成システム CLI エントリポイント"""

import typer
from dotenv import load_dotenv

load_dotenv(override=True)

from src.analyze import analyze
from src.clone import clone
from src.compose import compose
from src.download import download
from src.generate_character import generate_character
from src.generate_clip import generate_clip
from src.synthesize import synthesize
from src.transcribe import transcribe

app = typer.Typer(help="参考動画クローン生成システム", no_args_is_help=True)

app.command()(download)
app.command()(transcribe)
app.command()(analyze)
app.command("generate-character")(generate_character)
app.command("generate-clip")(generate_clip)
app.command()(synthesize)
app.command()(compose)
app.command()(clone)


if __name__ == "__main__":
    app()

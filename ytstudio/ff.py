"""ffmpeg/ffprobe yordamchilari."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class FfXato(RuntimeError):
    pass


def tekshir() -> None:
    for d in ("ffmpeg", "ffprobe"):
        if not shutil.which(d):
            raise FfXato(f"{d} topilmadi. O'rnating: https://ffmpeg.org/download.html (README ga qarang)")


def ishga(args: list[str], cwd: Path | None = None) -> None:
    r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args],
                       cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        raise FfXato(f"ffmpeg xatosi: {r.stderr.strip()[-600:]}")


def davom(yol: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", str(yol)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        raise FfXato(f"davomiylikni o'qib bo'lmadi: {yol}") from None


def olcham(yol: Path) -> tuple[int, int]:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height", "-of", "csv=p=0:s=x", str(yol)],
                       capture_output=True, text=True)
    w, h = r.stdout.strip().split("x")[:2]
    return int(w), int(h)

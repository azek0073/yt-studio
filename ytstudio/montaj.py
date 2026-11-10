"""Montaj: fon lavhalari + ovoz + kuydirilgan subtitr → tayyor MP4 (H.264/AAC, YouTube uchun)."""
from __future__ import annotations

from pathlib import Path

from . import ff


def _vaqt(t: float) -> str:
    sa = int(round(t * 100))
    return f"{sa // 360000}:{sa // 6000 % 60:02d}:{sa // 100 % 60:02d}.{sa % 100:02d}"


def ass_yoz(yol: Path, sub: list[tuple[float, float, str]], w: int, h: int, shrift: str) -> None:
    """ASS subtitr fayli. Tik videoda yirik va o'rtaroqda, yotiq videoda pastda."""
    tik = h > w
    hajm = int(h * 0.042) if tik else int(h * 0.058)
    past = int(h * 0.30) if tik else int(h * 0.08)
    bosh = (
        "[Script Info]\nScriptType: v4.00+\n"
        f"PlayResX: {w}\nPlayResY: {h}\nWrapStyle: 0\nScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV\n"
        f"Style: S,{shrift},{hajm},&H00FFFFFF,&H00000000,&H96000000,1,1,{max(2, hajm // 14)},1,2,"
        f"{int(w * 0.07)},{int(w * 0.07)},{past}\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Text\n"
    )
    toza = lambda x: x.replace("\\", "/").replace("{", "(").replace("}", ")").replace("\n", " ")
    yol.write_text(bosh + "".join(f"Dialogue: 0,{_vaqt(a)},{_vaqt(b)},S,{toza(x)}\n" for a, b, x in sub),
                   encoding="utf-8")


def yigish(fonlar: list[Path], ovoz: Path, sub: list[tuple[float, float, str]], chiqish: Path,
           w: int, h: int, shrift: str, ish: Path) -> float:
    """Tayyor videoni yozadi va uning davomiyligini qaytaradi.

    Chekka holat: fon lavhalari ovozdan qisqa bo'lsa — ro'yxat takrorlanadi; video aynan ovoz
    uzunligida kesiladi. ffmpeg `ish` papkasida ishga tushadi va fayllar nisbiy nom bilan beriladi —
    Windows yo'lidagi «C:» subtitr filtrini buzmasligi uchun.
    """
    ish.mkdir(parents=True, exist_ok=True)
    dav = ff.davom(ovoz)
    ass_yoz(ish / "sub.ass", sub, w, h, shrift)
    fon_dav = sum(ff.davom(f) for f in fonlar)
    takror = int(dav // max(fon_dav, 0.1)) + 1
    (ish / "fon.txt").write_text(
        "".join(f"file '{f.resolve().as_posix()}'\n" for f in fonlar * takror), encoding="utf-8")
    vaqtincha = chiqish.with_suffix(".tmp.mp4")
    ff.ishga(["-f", "concat", "-safe", "0", "-i", "fon.txt", "-i", str(ovoz.resolve()),
              "-vf", "eq=brightness=-0.10:saturation=0.9,subtitles=sub.ass",  # matn o'qilishi uchun fon xiralashadi
              "-map", "0:v:0", "-map", "1:a:0", "-t", f"{dav:.3f}",
              "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", "-r", "30",
              "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(vaqtincha.resolve())], cwd=ish)
    vaqtincha.replace(chiqish)
    return ff.davom(chiqish)

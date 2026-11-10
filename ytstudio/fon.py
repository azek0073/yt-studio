"""Fon videolari. Tartib: Pexels va/yoki Pixabay (kaliti bo'lsa) → `fon/` papkasidagi o'z videolaringiz → gradient.

Har manba bir xil ko'rinishga keltiriladi (o'lcham, 30 kadr/s, ≤ BOLAK soniya, ovozsiz) va keshlanadi.
Pexels litsenziyasi videolarni bepul ishlatishga ruxsat beradi (muallif ko'rsatish shart emas).
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

from . import ff

BOLAK = 7.0  # bitta fon lavhasining eng ko'p uzunligi, soniya


def _json(manzil: str, sarlavhalar: dict | None = None) -> dict:
    so = urllib.request.Request(manzil, headers={"User-Agent": "yt-studio", **(sarlavhalar or {})})
    with urllib.request.urlopen(so, timeout=30) as r:  # noqa: S310 — manzil kodda qat'iy (https)
        return json.load(r)


def _yuklab_ol(havola: str, qayerga: Path) -> None:
    so = urllib.request.Request(havola, headers={"User-Agent": "yt-studio"})
    with urllib.request.urlopen(so, timeout=120) as r, open(qayerga, "wb") as f:  # noqa: S310
        while bolak := r.read(1 << 20):
            f.write(bolak)


def _eng_mos(fayllar: list[dict], w: int, h: int) -> str | None:
    """Kerakli o'lchamni qoplaydigan ENG KICHIK faylni oladi (yuklash tez, sifat yetarli).
    fayllar: [{"url", "width", "height"}]."""
    fayllar = [f for f in fayllar if f.get("url") and f.get("width") and f.get("height")]
    if not fayllar:
        return None
    yuza = lambda f: f["width"] * f["height"]
    yetarli = [f for f in fayllar if f["width"] >= w * 0.66 and f["height"] >= h * 0.66]
    return (min(yetarli, key=yuza) if yetarli else max(fayllar, key=yuza))["url"]


def _pexels_nomzod(soz: str, w: int, h: int, kalit: str) -> list[dict]:
    q = urllib.parse.urlencode({"query": soz, "per_page": 15,
                                "orientation": "portrait" if h > w else "landscape"})
    javob = _json(f"https://api.pexels.com/videos/search?{q}", {"Authorization": kalit})
    out = []
    for v in javob.get("videos", []):
        havola = _eng_mos([{"url": f.get("link"), "width": f.get("width"), "height": f.get("height")}
                           for f in v.get("video_files", []) if f.get("file_type") == "video/mp4"], w, h)
        if havola:
            out.append({"kid": f"px{v['id']}", "havola": havola})
    return out


def _pixabay_nomzod(soz: str, w: int, h: int, kalit: str) -> list[dict]:
    """Pixabay (bepul kalit: https://pixabay.com/api/docs/). Video qidiruvida tik/yotiq filtri yo'q —
    yotiq video tik kadrga o'rtasidan qirqiladi (chetlari kesiladi)."""
    q = urllib.parse.urlencode({"key": kalit, "q": soz, "per_page": 15, "safesearch": "true"})
    javob = _json(f"https://pixabay.com/api/videos/?{q}")
    out = []
    for v in javob.get("hits", []):
        havola = _eng_mos(list((v.get("videos") or {}).values()), w, h)
        if havola:
            out.append({"kid": f"pb{v['id']}", "havola": havola})
    return out


def _normalla(manba: list[str], chiqish: Path, w: int, h: int) -> None:
    vaqtincha = chiqish.with_suffix(".tmp.mp4")
    ff.ishga([*manba, "-t", str(BOLAK), "-an", "-vf",
              f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},fps=30,setsar=1",
              "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p", str(vaqtincha)])
    vaqtincha.replace(chiqish)


def _gradient(kesh: Path, w: int, h: int) -> Path:
    out = kesh / f"gradient_{w}x{h}.mp4"
    if not out.exists():
        try:
            _normalla(["-f", "lavfi", "-i",
                       f"gradients=s={w}x{h}:d={BOLAK}:speed=0.02:c0=0x0f2027:c1=0x2c5364"], out, w, h)
        except ff.FfXato:  # eski ffmpeg'da `gradients` yo'q — bir rangli fon
            _normalla(["-f", "lavfi", "-i", f"color=c=0x16222a:s={w}x{h}:d={BOLAK}"], out, w, h)
    return out


def tayyorla(sozlar: list[str], w: int, h: int, kerak_soniya: float, s, ishlatilgan: list,
             log=print) -> list[Path]:
    """`kerak_soniya` ni qoplaydigan fon lavhalari ro'yxati. Yetmasa — bor lavhalar takrorlanadi."""
    norm = s.kesh / "fon"
    norm.mkdir(parents=True, exist_ok=True)
    kerak = max(1, int(kerak_soniya // BOLAK) + 1)
    out: list[Path] = []

    nomzodlar: list[dict] = []  # [{"kid": "px123", "havola": "https://..."}]
    for nom, kalit, qidir in (("Pexels", s.pexels_kalit, _pexels_nomzod),
                              ("Pixabay", s.pixabay_kalit, _pixabay_nomzod)):
        if not kalit:
            continue
        for soz in sozlar:
            try:
                nomzodlar += qidir(soz, w, h, kalit)
            except Exception as e:  # noqa: BLE001 — tarmoq/kalit xatosi: zaxira fonga o'tamiz
                log(f"  ⚠ {nom} «{soz}»: {e}")
    if nomzodlar:
        xom = s.kesh / "stok"
        xom.mkdir(parents=True, exist_ok=True)
        # Avval hali ishlatilmaganlar — videolar bir-biriga o'xshab qolmasin
        nomzodlar.sort(key=lambda v: v["kid"] in ishlatilgan)
        for v in nomzodlar:
            if len(out) >= kerak:
                break
            tayyor = norm / f"{v['kid']}_{w}x{h}.mp4"
            if tayyor in out:
                continue
            try:
                if not tayyor.exists():
                    manba = xom / f"{v['kid']}.mp4"
                    _yuklab_ol(v["havola"], manba)
                    _normalla(["-i", str(manba)], tayyor, w, h)
                    manba.unlink(missing_ok=True)  # xom fayl katta — saqlanmaydi
                out.append(tayyor)
                if v["kid"] not in ishlatilgan:
                    ishlatilgan.append(v["kid"])
            except Exception as e:  # noqa: BLE001
                log(f"  ⚠ fon {v['kid']}: {e}")

    if not out and s.fon.exists():
        for f in sorted(s.fon.iterdir()):
            if f.suffix.lower() in {".mp4", ".mov", ".mkv", ".webm"} and len(out) < kerak:
                tayyor = norm / f"oz_{f.stem}_{w}x{h}.mp4"
                try:
                    if not tayyor.exists():
                        _normalla(["-i", str(f)], tayyor, w, h)
                    out.append(tayyor)
                except ff.FfXato as e:
                    log(f"  ⚠ fon {f.name}: {e}")

    if not out:
        log("  ⚠ stok video yo'q (Pexels kaliti/tarmoq) — gradient fon ishlatildi")
        out.append(_gradient(norm, w, h))
    return out

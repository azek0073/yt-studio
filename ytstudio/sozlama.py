"""Sozlamalar: hammasi bitta joyda. Qiymatlar `.env` faylidan yoki muhit o'zgaruvchilaridan olinadi."""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

ILDIZ = Path(__file__).resolve().parent.parent  # yt-studio/


def _env_fayl(yol: Path) -> dict[str, str]:
    """Oddiy KEY=VALUE o'quvchi (qo'shimcha kutubxona kerak emas). `#` — izoh."""
    out: dict[str, str] = {}
    if not yol.exists():
        return out
    for qator in yol.read_text(encoding="utf-8").splitlines():
        qator = qator.strip()
        if not qator or qator.startswith("#") or "=" not in qator:
            continue
        k, v = qator.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


@dataclass
class Sozlama:
    ildiz: Path
    pixabay_kalit: str     # Pexels o'rniga/yoniga: https://pixabay.com/api/docs/
    pexels_kalit: str      # bo'sh bo'lsa: fon/ papkasidagi videolar, u ham bo'lmasa — gradient fon
    kalit_sozlar: str      # stok video qidiruvi (inglizcha, vergul bilan); matn faylida `kalit:` ustun turadi
    tts: str               # "edge" (Microsoft Edge ovozi, bepul) yoki "jim" (ovozsiz — faqat sinov uchun)
    ovoz: str              # uz-UZ-MadinaNeural (ayol) / uz-UZ-SardorNeural (erkak)
    ovoz_tezlik: str       # masalan "+0%", "+10%", "-5%"
    rils_soni: int
    video_soni: int
    rils_max_soniya: float  # rils shu uzunlikdan oshmaydi (gap o'rtasidan kesilmaydi)
    maxfiylik: str         # private | unlisted | public
    oraliq_soat: float     # `xizmat` rejimida ishga tushishlar orasi
    shrift: str
    toifa: str             # YouTube categoryId (22 — People & Blogs, 27 — Education)

    # Papkalar
    @property
    def matn(self) -> Path: return self.ildiz / "matn"
    @property
    def chiqish(self) -> Path: return self.ildiz / "chiqish"
    @property
    def kesh(self) -> Path: return self.ildiz / "kesh"
    @property
    def fon(self) -> Path: return self.ildiz / "fon"
    @property
    def holat(self) -> Path: return self.ildiz / "holat.json"
    @property
    def client_secret(self) -> Path: return self.ildiz / "client_secret.json"
    @property
    def token(self) -> Path: return self.ildiz / "token.json"


def yukla(ildiz: Path | None = None, **ustun) -> Sozlama:
    """Ustuvorlik: `ustun` argumentlari > muhit o'zgaruvchilari > .env > sukut."""
    ildiz = Path(ildiz or ILDIZ)
    e = {**_env_fayl(ildiz / ".env"), **os.environ}
    g = lambda k, d: str(ustun.get(k.lower(), e.get(k, d)))
    return Sozlama(
        ildiz=ildiz,
        pexels_kalit=g("PEXELS_API_KEY", ""),
        pixabay_kalit=g("PIXABAY_API_KEY", ""),
        kalit_sozlar=g("KALIT_SOZLAR", "nature, city, sky"),
        tts=g("TTS", "edge"),
        ovoz=g("OVOZ", "uz-UZ-MadinaNeural"),
        ovoz_tezlik=g("OVOZ_TEZLIK", "+0%"),
        rils_soni=int(g("RILS_SONI", 5)),
        video_soni=int(g("VIDEO_SONI", 3)),
        rils_max_soniya=float(g("RILS_MAX_SONIYA", 58)),
        maxfiylik=g("MAXFIYLIK", "private"),
        oraliq_soat=float(g("ORALIQ_SOAT", 12)),
        shrift=g("SHRIFT", "Arial" if sys.platform.startswith("win") else "DejaVu Sans"),
        toifa=g("TOIFA", "22"),
    )

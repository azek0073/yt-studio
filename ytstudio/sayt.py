"""Sayt (GitHub Pages) yig'ish: panel + tayyor videolar + ro'yxat (videolar.json).

    python -m ytstudio.sayt [--asos https://<egasi>.github.io/<repo>/] [--sinov]

Pages har safar saytni TO'LIQ almashtiradi, shuning uchun avvalgi to'plamlar eski saytdan qayta
yuklab olinadi va oxirgi SAQLASH ta to'plam saqlanadi (sayt hajmi cheklangan: ~1 GB).
Eski sayt hali yo'q bo'lsa (birinchi marta) yoki olinmasa — faqat yangi to'plam chiqadi.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from . import navbat, sozlama

SAQLASH = 3  # saytda turadigan to'plamlar soni (1 to'plam = 5 rils + 3 video)
BOSH = ('<!doctype html><html lang="uz"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        "<style>body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style></head><body>")


def _ol(manzil: str, vaqt: int = 60) -> bytes:
    so = urllib.request.Request(manzil, headers={"User-Agent": "yt-studio"})
    with urllib.request.urlopen(so, timeout=vaqt) as r:  # noqa: S310 — manzil: o'z Pages saytimiz
        return r.read()


def eski_toplamlar(asos: str, sayt: Path, log=print) -> list[dict]:
    """Eski saytdagi to'plamlarni (videolari bilan) yangi sayt papkasiga ko'chiradi."""
    if not asos:
        return []
    try:
        eski = json.loads(_ol(asos.rstrip("/") + "/videolar.json", 30)).get("toplamlar", [])
    except Exception as e:  # noqa: BLE001 — birinchi marta sayt yo'q (404): bu xato emas
        log(f"Eski sayt o'qilmadi ({e}) — faqat yangi to'plam chiqadi.")
        return []
    out = []
    for t in eski[: SAQLASH - 1]:
        try:
            for v in t["videolar"]:
                # Ro'yxat tashqaridan o'qiladi — fayl yo'li faqat kutilgan ko'rinishda bo'lsa yoziladi
                if not re.fullmatch(r"videolar/[\w-]+/[\w-]+\.mp4", v["fayl"]):
                    raise ValueError(f"kutilmagan yo'l: {v['fayl']}")
                joy = sayt / v["fayl"]
                joy.parent.mkdir(parents=True, exist_ok=True)
                joy.write_bytes(_ol(asos.rstrip("/") + "/" + v["fayl"], 180))
            out.append(t)
        except Exception as e:  # noqa: BLE001 — bitta eski to'plam olinmasa, qolgani chiqaveradi
            log(f"  ⚠ eski to'plam {t.get('id')}: {e}")
    return out


def yig(s, asos: str = "", sinov: bool = False, log=print) -> Path:
    sayt = s.ildiz / "sayt"
    if sayt.exists():
        shutil.rmtree(sayt)
    (sayt / "videolar").mkdir(parents=True)
    panel = (s.ildiz / "panel" / "yt-studio-panel.html").read_text(encoding="utf-8")
    (sayt / "index.html").write_text(BOSH + panel + "</body></html>", encoding="utf-8")

    toplamlar: list[dict] = []
    elementlar = [e for e in navbat.oqi(s.holat)["navbat"] if Path(e["fayl"]).exists()]
    if elementlar:
        tid = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
        videolar = []
        for e in elementlar:
            manba = Path(e["fayl"])
            nisbiy = f"videolar/{tid}/{manba.name}"
            (sayt / nisbiy).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(manba, sayt / nisbiy)
            videolar.append({"fayl": nisbiy, "tur": e["tur"], "dav": e.get("dav", 0), "sarlavha": e["sarlavha"],
                             "tavsif": e["tavsif"], "teglar": e["teglar"], "video_id": e.get("video_id", "")})
        toplamlar.append({"id": tid, "nom": manba.parent.name, "sinov": sinov, "videolar": videolar})
        log(f"Yangi to'plam {tid}: {len(videolar)} ta video")
    toplamlar += eski_toplamlar(asos, sayt, log)
    (sayt / "videolar.json").write_text(
        json.dumps({"yangilandi": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "toplamlar": toplamlar[:SAQLASH]}, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"Sayt: {sayt} — {len(toplamlar[:SAQLASH])} ta to'plam")
    return sayt


if __name__ == "__main__":
    a = sys.argv[1:]
    yig(sozlama.yukla(), asos=a[a.index("--asos") + 1] if "--asos" in a else "", sinov="--sinov" in a)

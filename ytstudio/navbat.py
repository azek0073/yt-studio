"""Holat (holat.json): qaysi videolar tayyor, qaysi biri yuklangan. Dastur to'xtab qolsa ham
qayta ishga tushganda davom etadi — video ikki marta yuklanmaydi."""
from __future__ import annotations

import json
import os
from pathlib import Path


class Kvota(RuntimeError):
    """Bugungi YouTube API kvotasi yoki kanalning kunlik yuklash chegarasi tugadi."""


def oqi(yol: Path) -> dict:
    h = json.loads(yol.read_text(encoding="utf-8")) if yol.exists() else {}
    h.setdefault("navbat", [])            # [{fayl, tur, sarlavha, tavsif, teglar, holat, video_id}]
    h.setdefault("fon_ishlatilgan", [])   # Pexels video id'lari
    return h


def yoz(yol: Path, h: dict) -> None:
    h["fon_ishlatilgan"] = h["fon_ishlatilgan"][-500:]
    vaqtincha = yol.with_suffix(".tmp")
    vaqtincha.write_text(json.dumps(h, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(vaqtincha, yol)  # atomar: yarim yozilgan holat qolmaydi


def kutayotgan(h: dict) -> list[dict]:
    return [x for x in h["navbat"] if x["holat"] == "kutmoqda"]

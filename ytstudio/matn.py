"""Matn: faylni o'qish, gaplarga ajratish, bo'laklash. AI yo'q — matn O'ZGARTIRILMAYDI.

Fayl ko'rinishi (bosh qism ixtiyoriy, bo'sh qatorgacha):

    sarlavha: Ipak yo'li tarixi
    kalit: desert, caravan, old city
    teglar: tarix, ipak yo'li

    Matnning o'zi shu yerdan boshlanadi. ...
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

BOSH_KALITLAR = {"sarlavha", "kalit", "teglar", "ovoz"}


@dataclass
class Hujjat:
    sarlavha: str
    gaplar: list[str]
    kalit: list[str] = field(default_factory=list)   # stok video qidiruv so'zlari (inglizcha)
    teglar: list[str] = field(default_factory=list)
    ovoz: str = ""


def gaplarga(matn: str) -> list[str]:
    """Gap chegarasi: . ! ? … dan keyingi bo'shliq. Qisqartma (masalan «A. Navoiy») bo'linib
    ketishi mumkin — bu faqat pauza joyiga ta'sir qiladi, matn yo'qolmaydi."""
    matn = re.sub(r"\s+", " ", matn).strip()
    if not matn:
        return []
    return [g.strip() for g in re.split(r"(?<=[.!?…])[\"»”)]*\s+", matn) if g.strip()]


def oqi(xom: str, nom: str = "") -> Hujjat:
    qatorlar = xom.replace("﻿", "").splitlines()
    bosh: dict[str, str] = {}
    i = 0
    while i < len(qatorlar):
        m = re.match(r"^\s*([A-Za-z]+)\s*:\s*(.*)$", qatorlar[i])
        if not m or m.group(1).lower() not in BOSH_KALITLAR:
            break
        bosh[m.group(1).lower()] = m.group(2).strip()
        i += 1
    gaplar = gaplarga("\n".join(qatorlar[i:]))
    royxat = lambda s: [x.strip() for x in s.split(",") if x.strip()]
    sarlavha = bosh.get("sarlavha") or nom or (gaplar[0][:60] if gaplar else "")
    return Hujjat(sarlavha, gaplar, royxat(bosh.get("kalit", "")), royxat(bosh.get("teglar", "")),
                  bosh.get("ovoz", ""))


def bolakla(gaplar: list[str], n: int) -> list[list[str]]:
    """Gaplarni tartibini saqlab, uzunligi taxminan teng n ta ketma-ket bo'lakka bo'ladi.
    Gap n dan kam bo'lsa — bo'lak ham kam chiqadi (bo'sh bo'lak to'qilmaydi)."""
    n = min(n, len(gaplar))
    if n <= 0:
        return []
    jami = sum(len(g) for g in gaplar)
    out: list[list[str]] = []
    joriy: list[str] = []
    yigindi = 0
    for i, g in enumerate(gaplar):
        joriy.append(g)
        yigindi += len(g)
        qolgan_gap = len(gaplar) - i - 1
        qolgan_bolak = n - len(out) - 1
        if len(out) < n - 1 and (yigindi >= jami * (len(out) + 1) / n or qolgan_gap == qolgan_bolak):
            out.append(joriy)
            joriy = []
    if joriy:
        out.append(joriy)
    return out


def iboralar(gap: str, max_belgi: int) -> list[str]:
    """Subtitr uchun: gapni ekranga sig'adigan qisqa iboralarga (so'z chegarasida) bo'ladi."""
    out: list[str] = []
    joriy = ""
    for soz in gap.split():
        if joriy and len(joriy) + 1 + len(soz) > max_belgi:
            out.append(joriy)
            joriy = soz
        else:
            joriy = f"{joriy} {soz}".strip()
    if joriy:
        out.append(joriy)
    return out


def subtitr(gaplar: list[str], davomlar: list[float], max_belgi: int) -> list[tuple[float, float, str]]:
    """Har gapning o'lchangan ovoz davomiyligi ichida iboralar belgi soniga mutanosib taqsimlanadi.
    (So'z darajasidagi aniq vaqt emas — gap chegaralari aniq, ichkarisi taxminiy.)"""
    out: list[tuple[float, float, str]] = []
    t = 0.0
    for gap, d in zip(gaplar, davomlar):
        ib = iboralar(gap, max_belgi)
        jami = sum(len(x) for x in ib) or 1
        boshi = t
        for x in ib:
            uzun = d * len(x) / jami
            out.append((round(boshi, 3), round(boshi + uzun, 3), x))
            boshi += uzun
        t += d
    return out

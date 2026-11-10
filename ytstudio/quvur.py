"""Asosiy jarayon: matn → bo'laklar → ovoz → fon → montaj → navbat → YouTube."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

from . import ff, fon, matn, montaj, navbat, ovoz
from .matn import Hujjat
from .navbat import Kvota

RILS = (1080, 1920)   # tik 9:16 — YouTube Shorts
VIDEO = (1920, 1080)  # yotiq 16:9


def _toza(x: str) -> str:
    return re.sub(r"[<>]", "", x).strip()  # YouTube sarlavha/tavsifda < > ni qabul qilmaydi


def _sarlavha(asos: str, i: int, jami: int, rils: bool) -> str:
    dum = (f" — {i}-qism" if jami > 1 else "") + (" #Shorts" if rils else "")
    return _toza(asos)[: 100 - len(dum)].rstrip() + dum  # YouTube chegarasi: 100 belgi


def _bitta(gaplar: list[str], tur: str, i: int, h: Hujjat, s, holat: dict, papka: Path, log) -> dict | None:
    w, hh = RILS if tur == "rils" else VIDEO
    ovoz_nomi = h.ovoz or s.ovoz
    wavlar, davomlar, olingan = [], [], []
    for g in gaplar:
        wav, d = ovoz.gap_ovozi(g, s.kesh / "ovoz", s.tts, ovoz_nomi, s.ovoz_tezlik)
        # Rils chegarasi: gap o'rtasidan KESILMAYDI — sig'magan gapdan boshlab qolgani shu rilsga kirmaydi
        # (to'liq matn baribir qisqa videolarda bor). Birinchi gap har doim olinadi.
        if tur == "rils" and olingan and sum(davomlar) + d > s.rils_max_soniya:
            break
        wavlar.append(wav)
        davomlar.append(d)
        olingan.append(g)
    if not olingan:
        return None
    if tur == "rils" and sum(davomlar) > s.rils_max_soniya:
        log(f"  ⚠ rils {i}: birinchi gapning o'zi {sum(davomlar):.0f} s — chegaradan uzun (gapni qisqartiring)")

    ish = s.kesh / "ish" / f"{papka.name}_{tur}{i}"
    ish.mkdir(parents=True, exist_ok=True)
    ovoz.birlashtir(wavlar, ish / "ovoz.wav")
    sozlar = h.kalit or [x.strip() for x in s.kalit_sozlar.split(",") if x.strip()]
    if sozlar:  # har videoga boshqa qidiruv so'zidan boshlanadi — fonlar xilma-xil bo'lsin
        k = (i - 1) % len(sozlar)
        sozlar = sozlar[k:] + sozlar[:k]
    fonlar = fon.tayyorla(sozlar, w, hh, sum(davomlar), s, holat["fon_ishlatilgan"], log)
    sub = matn.subtitr(olingan, davomlar, 24 if tur == "rils" else 46)
    chiqish = papka / f"{tur}_{i}.mp4"
    dav = montaj.yigish(fonlar, ish / "ovoz.wav", sub, chiqish, w, hh, s.shrift, ish)
    shutil.rmtree(ish, ignore_errors=True)
    log(f"  ✓ {chiqish.name}: {dav:.0f} s, {len(olingan)}/{len(gaplar)} gap")
    return {"fayl": str(chiqish), "tur": tur, "dav": round(dav, 1), "matn": " ".join(olingan)}


def tayyorla(s, log=print) -> int:
    """`matn/` dagi navbatdagi (nomi bo'yicha birinchi) faylni videolarga aylantiradi.
    Qaytaradi: tayyorlangan videolar soni (yangi matn bo'lmasa 0 — hech narsa to'qilmaydi)."""
    ff.tekshir()
    s.matn.mkdir(parents=True, exist_ok=True)
    fayllar = sorted(f for f in s.matn.iterdir() if f.is_file() and f.suffix.lower() == ".txt")
    if not fayllar:
        log(f"Yangi matn yo'q — {s.matn} papkasiga .txt fayl qo'ying.")
        return 0
    fayl = fayllar[0]
    h = matn.oqi(fayl.read_text(encoding="utf-8"), fayl.stem)
    if not h.gaplar:
        log(f"⚠ {fayl.name}: matn bo'sh — o'tkazildi.")
        _kochir(fayl, s.matn / "xato")
        return 0
    holat = navbat.oqi(s.holat)
    papka = s.chiqish / fayl.stem
    papka.mkdir(parents=True, exist_ok=True)
    log(f"Matn: {fayl.name} — {len(h.gaplar)} gap, sarlavha: «{h.sarlavha}»")

    reja = [("rils", b) for b in matn.bolakla(h.gaplar, s.rils_soni)] + \
           [("video", b) for b in matn.bolakla(h.gaplar, s.video_soni)]
    jami = {t: sum(1 for x, _ in reja if x == t) for t in ("rils", "video")}
    for tur, kerak in (("rils", s.rils_soni), ("video", s.video_soni)):
        if jami[tur] < kerak:
            log(f"  ⚠ matnda gap kam: {tur} {kerak} ta o'rniga {jami[tur]} ta chiqadi")

    soni = 0
    sanoq = {"rils": 0, "video": 0}
    for tur, gaplar in reja:
        sanoq[tur] += 1
        i = sanoq[tur]
        try:
            r = _bitta(gaplar, tur, i, h, s, holat, papka, log)
        except Exception as e:  # noqa: BLE001 — bitta video xatosi qolganlarini to'xtatmasin
            log(f"  ✗ {tur} {i}: {e}")
            continue
        if not r:
            continue
        teglar = h.teglar[:15]
        xesh = " ".join("#" + re.sub(r"\W+", "", t) for t in teglar if re.sub(r"\W+", "", t))
        holat["navbat"].append({
            "fayl": r["fayl"], "tur": tur, "dav": r["dav"],
            "sarlavha": _sarlavha(h.sarlavha, i, jami[tur], tur == "rils"),
            "tavsif": _toza(r["matn"])[:4500] + (f"\n\n{xesh}" if xesh else ""),
            "teglar": teglar, "holat": "kutmoqda", "video_id": "",
        })
        soni += 1
        navbat.yoz(s.holat, holat)  # har videodan keyin — uzilib qolsa tayyorlangani yo'qolmaydi
    if soni:
        _kochir(fayl, s.matn / "tayyor")
    else:
        log("✗ Hech bir video tayyorlanmadi — matn fayli joyida qoldi (sababi yuqorida).")
    return soni


def _kochir(fayl: Path, qayerga: Path) -> None:
    qayerga.mkdir(parents=True, exist_ok=True)
    fayl.replace(qayerga / fayl.name)


def yukla(s, yuklovchi=None, log=print) -> tuple[int, int]:
    """Navbatdagi videolarni yuklaydi. Qaytaradi: (yuklandi, qoldi)."""
    holat = navbat.oqi(s.holat)
    kut = navbat.kutayotgan(holat)
    if not kut:
        log("Yuklash navbati bo'sh.")
        return 0, 0
    if yuklovchi is None:
        try:
            from .yuklash import yuklovchi as yasash
        except ImportError:
            log(f"  ⏸ YouTube'ga yuklash moduli hali ulanmagan — {len(kut)} ta video navbatda, "
                f"fayllar: {s.chiqish}")
            return 0, len(kut)
        yuklovchi = yasash(s)
    n = 0
    for el in kut:
        if not Path(el["fayl"]).exists():
            el["holat"] = "fayl yo'q"
            log(f"  ✗ {el['fayl']}: fayl topilmadi — navbatdan chiqarildi")
            continue
        try:
            el["video_id"] = yuklovchi(el)
        except Kvota:
            log("  ⏸ YouTube kvotasi/kunlik chegarasi tugadi — qolganlari keyingi safar yuklanadi.")
            break
        except Exception as e:  # noqa: BLE001
            log(f"  ✗ {Path(el['fayl']).name}: {e}")
            continue
        el["holat"] = "yuklandi"
        n += 1
        navbat.yoz(s.holat, holat)  # har yuklashdan keyin — uzilsa ikki marta yuklanmaydi
        log(f"  ↑ {el['sarlavha']} → https://youtu.be/{el['video_id']}")
    navbat.yoz(s.holat, holat)
    return n, len(navbat.kutayotgan(holat))

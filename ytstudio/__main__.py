"""Buyruqlar:  python -m ytstudio <buyruq>

  kirish     YouTube hisobiga bir marta ruxsat berish (brauzer ochiladi)
  tayyorla   navbatdagi matndan videolar yasash (yuklamaydi)
  yukla      tayyor videolarni YouTube'ga yuklash
  ishla      tayyorla + yukla (bir marta)
  xizmat     to'xtovsiz: har ORALIQ_SOAT (12) soatda `ishla`
  holat      navbat holati
"""
from __future__ import annotations

import sys
import time
from datetime import datetime

from . import navbat, quvur, sozlama


def _ishla(s) -> None:
    quvur.tayyorla(s)
    try:
        quvur.yukla(s)
    except Exception as e:  # noqa: BLE001 — yuklash xatosi tayyor videolarni yo'qotmaydi (navbatda qoladi)
        print(f"✗ Yuklash: {e}")


def main(argv: list[str]) -> int:
    buyruq = argv[0] if argv else ""
    s = sozlama.yukla()
    if buyruq == "kirish":
        try:
            from .yuklash import hisob
        except ImportError:
            print("YouTube'ga yuklash moduli hali ulanmagan (README: «Hozirgi holat»).")
            return 1
        hisob(s, interaktiv=True)
        print("✓ YouTube'ga ruxsat berildi.")
    elif buyruq == "tayyorla":
        quvur.tayyorla(s)
    elif buyruq == "yukla":
        quvur.yukla(s)
    elif buyruq == "ishla":
        _ishla(s)
    elif buyruq == "xizmat":
        while True:
            print(f"\n=== {datetime.now():%Y-%m-%d %H:%M} ===")
            try:
                _ishla(s)
            except Exception as e:  # noqa: BLE001 — xizmat bitta xatodan to'xtab qolmasin
                print(f"✗ {e}")
            print(f"Keyingi ishga tushish {s.oraliq_soat:g} soatdan keyin. To'xtatish: Ctrl+C")
            time.sleep(s.oraliq_soat * 3600)
    elif buyruq == "holat":
        h = navbat.oqi(s.holat)
        for el in h["navbat"][-30:]:
            print(f"{el['holat']:<10} {el['tur']:<5} {el.get('dav', 0):>5.0f}s  {el['sarlavha']}")
        print(f"Jami: {len(h['navbat'])}, kutmoqda: {len(navbat.kutayotgan(h))}")
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        print("\nTo'xtatildi.")

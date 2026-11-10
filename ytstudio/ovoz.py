"""Ovoz (TTS). Har gap alohida o'qiladi — shunda gap davomiyligi ANIQ o'lchanadi (subtitr vaqti shundan).

"edge" — Microsoft Edge onlayn ovozi (`edge-tts` kutubxonasi; bepul, lekin norasmiy xizmat: Microsoft
          o'zgartirsa ishlamay qolishi mumkin; internet kerak).
"jim"  — ovozsiz (faqat sinov uchun): davomiylik belgi soniga qarab taxmin qilinadi.
"""
from __future__ import annotations

import asyncio
import hashlib
import time
from pathlib import Path

from . import ff

PAUZA = 0.25  # gaplar orasidagi tin olish, soniya


def _edge(matn: str, yol: Path, ovoz: str, tezlik: str) -> None:
    import edge_tts  # kech import: "jim" rejimda kutubxona shart emas
    xato: Exception | None = None
    for urinish in range(3):  # tarmoq uzilishiga qarshi
        try:
            asyncio.run(edge_tts.Communicate(matn, ovoz, rate=tezlik).save(str(yol)))
            if yol.exists() and yol.stat().st_size > 0:
                return
        except Exception as e:  # noqa: BLE001 — kutubxona turli xato tashlaydi
            xato = e
        time.sleep(2 * (urinish + 1))
    raise RuntimeError(f"ovoz yaratilmadi ({ovoz}): {xato}")


def gap_ovozi(matn: str, kesh: Path, tts: str, ovoz: str, tezlik: str) -> tuple[Path, float]:
    """Bitta gap → WAV (44,1 kHz mono, oxirida PAUZA) va uning davomiyligi. Keshlanadi."""
    kesh.mkdir(parents=True, exist_ok=True)
    kalit = hashlib.sha1(f"{tts}|{ovoz}|{tezlik}|{matn}".encode()).hexdigest()[:20]
    wav = kesh / f"{kalit}.wav"
    if not wav.exists():
        vaqtincha = kesh / f"{kalit}.tmp.wav"
        if tts == "jim":
            ff.ishga(["-f", "lavfi", "-t", f"{max(1.0, len(matn) / 15):.2f}",
                      "-i", "anullsrc=r=44100:cl=mono", str(vaqtincha)])
        else:
            mp3 = kesh / f"{kalit}.mp3"
            _edge(matn, mp3, ovoz, tezlik)
            ff.ishga(["-i", str(mp3), "-af", f"apad=pad_dur={PAUZA}", "-ar", "44100", "-ac", "1",
                      str(vaqtincha)])
            mp3.unlink(missing_ok=True)
        vaqtincha.replace(wav)  # yarim yozilgan fayl keshga tushmasin
    return wav, ff.davom(wav)


def birlashtir(wavlar: list[Path], chiqish: Path) -> None:
    royxat = chiqish.with_suffix(".txt")
    royxat.write_text("".join(f"file '{w.resolve().as_posix()}'\n" for w in wavlar), encoding="utf-8")
    ff.ishga(["-f", "concat", "-safe", "0", "-i", str(royxat), "-c", "copy", str(chiqish)])
    royxat.unlink(missing_ok=True)

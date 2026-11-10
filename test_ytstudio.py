"""Oflayn sinov:  python test_ytstudio.py   (internet, kalit va YouTube kerak emas; ffmpeg kerak)

Tekshiradi: matn o'zgarmasligi, bo'laklash, subtitr vaqti, to'liq montaj (ovozsiz TTS + gradient fon),
rils chegarasi, navbat va kvota tugaganda to'xtash/davom etish.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ytstudio import ff, matn, navbat, quvur, sozlama  # noqa: E402

NAMUNA = (Path(__file__).parent / "namuna.txt").read_text(encoding="utf-8")


def sinov_matn() -> None:
    h = matn.oqi(NAMUNA, "namuna")
    assert h.sarlavha == "Suv haqida qiziqarli faktlar"
    assert h.kalit == ["water", "ocean", "rain", "river"] and h.teglar == ["suv", "faktlar", "tabiat"]
    assert len(h.gaplar) == 14 and h.gaplar[0] == "Suv — Yerdagi hayotning asosi."
    # Bosh qismsiz matn: sarlavha fayl nomidan
    assert matn.oqi("Bir gap. Ikkinchi gap!", "nom").sarlavha == "nom"
    # Bo'laklash: tartib saqlanadi, hech bir gap yo'qolmaydi va o'zgarmaydi
    for n in (1, 3, 5, 14, 20):
        b = matn.bolakla(h.gaplar, n)
        assert len(b) == min(n, 14) and all(b), n
        assert [g for x in b for g in x] == h.gaplar, n
    uzun = [sum(len(g) for g in x) for x in matn.bolakla(h.gaplar, 3)]
    assert max(uzun) < 2 * min(uzun), uzun  # taxminan teng
    assert matn.bolakla([], 3) == []
    # Subtitr: vaqtlar ketma-ket, gap davomiyligidan chiqmaydi, so'zlar yo'qolmaydi
    sub = matn.subtitr(h.gaplar[:3], [2.0, 4.0, 3.0], 24)
    assert abs(sub[-1][1] - 9.0) < 0.01 and all(a < b for a, b, _ in sub)
    assert all(sub[i][1] <= sub[i + 1][0] + 0.002 for i in range(len(sub) - 1))
    assert " ".join(x for *_, x in sub) == " ".join(h.gaplar[:3])
    assert all(len(x) <= 24 for *_, x in sub)
    print("✓ matn, bo'laklash, subtitr")


def sinov_montaj() -> None:
    ildiz = Path(tempfile.mkdtemp(prefix="ytstudio_"))
    try:
        (ildiz / "matn").mkdir()
        (ildiz / "matn" / "01_suv.txt").write_text(NAMUNA, encoding="utf-8")
        # tts="jim": ovozsiz; Pexels kaliti yo'q → gradient fon. Rils chegarasi ataylab kichik (8 s).
        s = sozlama.yukla(ildiz, tts="jim", pexels_api_key="", rils_max_soniya=8)
        loglar: list[str] = []
        assert quvur.tayyorla(s, loglar.append) == 8, loglar
        h = navbat.oqi(s.holat)
        assert [x["tur"] for x in h["navbat"]] == ["rils"] * 5 + ["video"] * 3
        for el in h["navbat"]:
            w, hh = ff.olcham(Path(el["fayl"]))
            d = ff.davom(Path(el["fayl"]))
            assert len(el["sarlavha"]) <= 100 and abs(d - el["dav"]) < 0.2
            if el["tur"] == "rils":
                assert (w, hh) == (1080, 1920) and d <= 8.3, (w, hh, d)
                assert el["sarlavha"].endswith("#Shorts")
            else:
                assert (w, hh) == (1920, 1080), (w, hh)
        # Qisqa videolar birgalikda TO'LIQ matnni beradi (o'zgarishsiz)
        toliq = " ".join(x["tavsif"].split("\n\n#")[0] for x in h["navbat"] if x["tur"] == "video")
        assert toliq == " ".join(matn.oqi(NAMUNA).gaplar)
        assert (ildiz / "matn" / "tayyor" / "01_suv.txt").exists()
        assert quvur.tayyorla(s, loglar.append) == 0  # yangi matn yo'q — hech narsa to'qilmaydi
        print("✓ montaj: 5 rils (1080×1920) + 3 video (1920×1080)")

        # Yuklash: 3-videoda kvota tugaydi → to'xtaydi, navbat saqlanadi, keyingi safar davom etadi
        yuklangan: list[str] = []

        def soxta(el: dict) -> str:
            if len(yuklangan) == 3 and not soxta.ochiq:
                raise navbat.Kvota("quotaExceeded")
            yuklangan.append(el["fayl"])
            return f"id{len(yuklangan)}"

        soxta.ochiq = False
        assert quvur.yukla(s, soxta, loglar.append) == (3, 5)
        soxta.ochiq = True
        assert quvur.yukla(s, soxta, loglar.append) == (5, 0)
        assert len(set(yuklangan)) == 8  # hech biri ikki marta yuklanmadi
        assert quvur.yukla(s, soxta, loglar.append) == (0, 0)
        print("✓ navbat: kvota tugasa to'xtaydi, keyin davom etadi, takror yuklamaydi")
    finally:
        shutil.rmtree(ildiz, ignore_errors=True)


def sinov_yuklash() -> None:
    """Haqiqiy YouTube'ga ulanmaydi: faqat kvota xatosini tanish va so'rov tanasi (soxta xizmat bilan)."""
    try:
        from googleapiclient import discovery
        from googleapiclient.errors import HttpError
    except ImportError:
        print("– yuklash sinovi o'tkazildi (google kutubxonalari o'rnatilmagan)")
        return
    import json
    from types import SimpleNamespace
    from ytstudio import yuklash

    def xato(kod: int, sabab: str) -> HttpError:
        tana = json.dumps({"error": {"code": kod, "message": "x", "errors": [{"reason": sabab}]}}).encode()
        return HttpError(SimpleNamespace(status=kod, reason="x"), tana)

    assert yuklash.kvota_xatosimi(xato(403, "quotaExceeded"))
    assert yuklash.kvota_xatosimi(xato(400, "uploadLimitExceeded"))
    assert not yuklash.kvota_xatosimi(xato(400, "invalidTitle"))
    assert not yuklash.kvota_xatosimi(RuntimeError("tarmoq uzildi"))

    ildiz = Path(tempfile.mkdtemp(prefix="ytstudio_"))
    try:
        s = sozlama.yukla(ildiz, maxfiylik="unlisted")
        # Kirilmagan holat: brauzer ochilmaydi, aniq xabar chiqadi
        try:
            yuklash.hisob(s)
            raise AssertionError("kirilmagan holatda xato kutilgan edi")
        except RuntimeError as e:
            assert "kirish" in str(e)

        # Soxta YouTube xizmati: so'rov tanasi va kvota xatosining Kvota ga aylanishi
        korilgan: dict = {}

        class Sorov:
            def __init__(self, x): self.x = x
            def next_chunk(self, num_retries=0):
                if self.x:
                    raise self.x
                return None, {"id": "abc123"}

        class Soxta:
            xato_ = None
            def videos(self): return self
            def insert(self, part, body, media_body):
                korilgan.update(part=part, body=body)
                return Sorov(Soxta.xato_)

        asl_build, asl_hisob = discovery.build, yuklash.hisob
        discovery.build = lambda *a, **k: Soxta()
        yuklash.hisob = lambda s, interaktiv=False: None
        try:
            fayl = ildiz / "v.mp4"
            fayl.write_bytes(b"0" * 10)
            el = {"fayl": str(fayl), "sarlavha": "S", "tavsif": "T", "teglar": ["a"]}
            yukla = yuklash.yuklovchi(s)
            assert yukla(el) == "abc123"
            assert korilgan["body"]["status"] == {"privacyStatus": "unlisted", "selfDeclaredMadeForKids": False}
            assert korilgan["body"]["snippet"]["title"] == "S"
            Soxta.xato_ = xato(403, "quotaExceeded")
            try:
                yukla(el)
                raise AssertionError("Kvota kutilgan edi")
            except navbat.Kvota:
                pass
        finally:
            discovery.build, yuklash.hisob = asl_build, asl_hisob
    finally:
        shutil.rmtree(ildiz, ignore_errors=True)
    print("✓ yuklash: so'rov tanasi, kvota xatosi → navbat to'xtaydi (soxta YouTube bilan)")


def sinov_stok() -> None:
    """Stok manbalar (soxta javob bilan, internet yo'q): fayl tanlash, kesh, takrorlamaslik, xatoda zaxira."""
    from ytstudio import fon
    assert fon._eng_mos([{"url": "k", "width": 640, "height": 360}, {"url": "o", "width": 1280, "height": 720},
                         {"url": "y", "width": 3840, "height": 2160}], 1920, 1080) == "o"
    assert fon._eng_mos([{"url": "k", "width": 640, "height": 360}], 1920, 1080) == "k"
    assert fon._eng_mos([{"url": "", "width": 0, "height": 0}], 1920, 1080) is None

    ildiz = Path(tempfile.mkdtemp(prefix="ytstudio_"))
    asl = fon._json, fon._yuklab_ol
    try:
        namuna = ildiz / "n.mp4"
        ff.ishga(["-f", "lavfi", "-i", "testsrc=s=640x360:d=2:r=30", "-pix_fmt", "yuv420p", str(namuna)])
        sorovlar: list[str] = []

        def soxta_json(manzil, sarlavhalar=None):
            sorovlar.append(manzil)
            assert manzil.startswith("https://pixabay.com/api/videos/?") and "key=K1" in manzil
            return {"hits": [{"id": i, "videos": {"medium": {"url": f"https://x/{i}.mp4", "width": 1280,
                                                                "height": 720, "size": 1},
                                                  "tiny": {"url": "", "width": 0, "height": 0}}}
                             for i in (11, 12, 13)]}

        fon._json = soxta_json
        fon._yuklab_ol = lambda havola, qayerga: shutil.copy(namuna, qayerga)
        s = sozlama.yukla(ildiz, pexels_api_key="", pixabay_api_key="K1")
        ishlatilgan: list = []
        a = fon.tayyorla(["water"], 1080, 1920, 10, s, ishlatilgan, lambda *_: None)
        assert len(a) == 2 and ishlatilgan == ["pb11", "pb12"], (a, ishlatilgan)
        assert ff.olcham(a[0]) == (1080, 1920)
        # Keyingi video: avval ishlatilmagan pb13 olinadi
        b = fon.tayyorla(["water"], 1080, 1920, 3, s, ishlatilgan, lambda *_: None)
        assert b[0].name.startswith("pb13_"), b
        # Xizmat xato bersa — dastur to'xtamaydi, gradient fonga o'tadi
        def yiqil(*_a, **_k): raise OSError("tarmoq yo'q")
        fon._json = yiqil
        loglar: list[str] = []
        c = fon.tayyorla(["sky"], 1920, 1080, 3, s, [], loglar.append)
        assert c[0].name.startswith("gradient_") and any("Pixabay" in x for x in loglar), loglar
    finally:
        fon._json, fon._yuklab_ol = asl
        shutil.rmtree(ildiz, ignore_errors=True)
    print("✓ stok video: Pixabay javobi, fayl tanlash, takrorlamaslik, xatoda gradient (soxta xizmat bilan)")


if __name__ == "__main__":
    sinov_matn()
    sinov_stok()
    sinov_yuklash()
    sinov_montaj()
    print("Hammasi o'tdi.")

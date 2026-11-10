"""YouTube'ga yuklash (YouTube Data API v3, OAuth).

Bir marta: `python -m ytstudio kirish` — brauzerda Google hisobiga ruxsat beriladi, `token.json` saqlanadi
(faqat shu kompyuterda; repoga yozilmaydi — .gitignore). Ruxsat doirasi eng tor: faqat video yuklash.
Kvota tugasa `Kvota` xatosi — navbat saqlanadi, keyingi ishga tushishda davom etadi.
"""
from __future__ import annotations

from pathlib import Path

from .navbat import Kvota

RUXSAT = ["https://www.googleapis.com/auth/youtube.upload"]
KVOTA_SABABLARI = {"quotaExceeded", "dailyLimitExceeded", "uploadLimitExceeded", "rateLimitExceeded",
                   "userRateLimitExceeded"}


def hisob(s, interaktiv: bool = False):
    """Saqlangan ruxsatni o'qiydi (muddati o'tgan bo'lsa yangilaydi). `interaktiv` — brauzerda kirish."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    c = Credentials.from_authorized_user_file(str(s.token), RUXSAT) if s.token.exists() else None
    if c and c.expired and c.refresh_token:
        c.refresh(Request())
    if not c or not c.valid:
        if not interaktiv:
            raise RuntimeError("YouTube'ga kirilmagan. Avval: python -m ytstudio kirish")
        if not s.client_secret.exists():
            raise RuntimeError(f"{s.client_secret.name} topilmadi — README dagi «YouTube sozlash» bo'limiga qarang")
        from google_auth_oauthlib.flow import InstalledAppFlow
        c = InstalledAppFlow.from_client_secrets_file(str(s.client_secret), RUXSAT).run_local_server(port=0)
    s.token.write_text(c.to_json(), encoding="utf-8")
    try:
        s.token.chmod(0o600)  # faqat egasi o'qiy olsin (Windows'da ta'sirsiz)
    except OSError:
        pass
    return c


def kvota_xatosimi(e: Exception) -> bool:
    """Google xatosi kvota/kunlik chegara tufaylimi (shunda navbat to'xtaydi, video yo'qolmaydi)."""
    tafsilot = getattr(e, "error_details", None) or []
    sabablar = {d.get("reason") for d in tafsilot if isinstance(d, dict)}
    return bool(sabablar & KVOTA_SABABLARI) or any(k in str(e) for k in KVOTA_SABABLARI)


def yuklovchi(s):
    """(navbat elementi) → video_id funksiyasini qaytaradi."""
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload

    yt = build("youtube", "v3", credentials=hisob(s), cache_discovery=False)

    def yukla(el: dict) -> str:
        tana = {
            "snippet": {"title": el["sarlavha"], "description": el["tavsif"], "tags": el["teglar"],
                        "categoryId": s.toifa},
            "status": {"privacyStatus": s.maxfiylik, "selfDeclaredMadeForKids": False},
        }
        media = MediaFileUpload(str(Path(el["fayl"])), mimetype="video/mp4", chunksize=8 * 1024 * 1024,
                                resumable=True)  # bo'laklab: tarmoq uzilsa davom etadi
        sorov = yt.videos().insert(part="snippet,status", body=tana, media_body=media)
        try:
            javob = None
            while javob is None:
                _, javob = sorov.next_chunk(num_retries=5)
            return javob["id"]
        except HttpError as e:
            if kvota_xatosimi(e):
                raise Kvota(str(e)) from e
            raise

    return yukla

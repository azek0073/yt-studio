# YT-Studio — matndan YouTube rils va qisqa video

Siz matn yozasiz — dastur o'zi **5 ta rils (Shorts, tik 1080×1920)** va **3 ta qisqa video (yotiq 1920×1080)**
tayyorlaydi: o'zbekcha diktor ovozi, ekranda subtitr, fonida stok video. Har 12 soatda bitta matn.

Matn **o'zgartirilmaydi** (AI yo'q): faqat gap chegaralari bo'yicha bo'laklanadi.

## Hozirgi holat (halol)

| Qism | Holat |
|---|---|
| Matnni o'qish, bo'laklash, subtitr | ✅ ishlaydi, sinovdan o'tgan |
| Montaj (ffmpeg): 5 rils + 3 video | ✅ ishlaydi, sinovdan o'tgan |
| Navbat (uzilsa davom etadi, takror yuklamaydi, kvota tugasa kutadi) | ✅ sinovdan o'tgan (soxta yuklovchi bilan) |
| O'zbekcha ovoz (`edge-tts`) | ⚠ yozilgan, lekin **jonli sinalmagan** (ishlab chiqish muhitida tarmoq yopiq edi) |
| Stok video (Pexels, Pixabay) | ⚠ yozilgan, lekin **jonli sinalmagan** (shu sabab) |
| YouTube'ga avtomatik yuklash (`ytstudio/yuklash.py`) | ⚠ yozilgan, lekin **umuman ishga tushirilmagan**: na haqiqiy YouTube bilan, na soxta xizmat bilan (ishlab chiqish muhitida Google kutubxonalarini o'rnatib bo'lmadi). Sinov `test_ytstudio.py` da bor — kutubxonalar o'rnatilgan kompyuterda o'zi ishlaydi |

## O'rnatish (bir marta)

1. **Python 3.10+** va **ffmpeg** (libass bilan — odatiy yig'malarda bor):
   - Windows: `winget install Gyan.FFmpeg` · Ubuntu: `sudo apt install ffmpeg` · macOS: `brew install ffmpeg`
2. Kutubxona:
   ```bash
   pip install -r requirements.txt
   ```
3. Sozlama: `.env` faylini yarating (hammasi ixtiyoriy):
   ```
   PIXABAY_API_KEY=...           # bepul: https://pixabay.com/api/docs/ (ro'yxatdan o'tgach sahifada ko'rinadi)
   PEXELS_API_KEY=...            # ixtiyoriy: https://www.pexels.com/api/ (2026-11 da yangi kalit berish to'xtatilgan)
   KALIT_SOZLAR=nature, city, sky   # stok video qidiruvi, INGLIZCHA
   OVOZ=uz-UZ-MadinaNeural       # ayol; erkak: uz-UZ-SardorNeural
   OVOZ_TEZLIK=+0%
   RILS_SONI=5
   VIDEO_SONI=3
   RILS_MAX_SONIYA=58
   ORALIQ_SOAT=12
   MAXFIYLIK=private             # private | unlisted | public
   ```

## YouTube sozlash (bir marta)

1. https://console.cloud.google.com → yangi loyiha → «APIs & Services» → «Library» → **YouTube Data API v3** → Enable.
2. «OAuth consent screen»: turi External; «Test users» ga o'z Google pochtangizni qo'shing.
3. «Credentials» → «Create credentials» → «OAuth client ID» → turi **Desktop app** → JSON'ni yuklab oling
   va `client_secret.json` nomi bilan saqlang (repoga yozilmaydi).
4. Kirish (brauzer ochiladi, kanalingizni tanlab ruxsat bering):
   ```bash
   python -m ytstudio kirish
   ```
   Ruxsat `token.json` da saqlanadi; doirasi faqat video yuklash (`youtube.upload`).
   Loyiha «Testing» holatida bo'lsa Google ruxsatni 7 kunda bekor qiladi — `kirish` ni qayta bajarasiz
   (doimiy bo'lishi uchun consent screen'ni «In production» ga o'tkazing).
5. Avval `MAXFIYLIK=private` bilan bitta sinov yuklang va YouTube Studio'da tekshiring.

## Ishlatish

1. `matn/` papkasiga `.txt` fayl qo'ying (bir fayl = bir 12 soatlik to'plam; nomi bo'yicha navbat:
   `01_suv.txt`, `02_...txt`). Namuna: `namuna.txt` (sinab ko‘rish uchun `matn/` ga nusxalang).

   ```
   sarlavha: Suv haqida qiziqarli faktlar
   kalit: water, ocean, rain          ← fon videosi qidiruvi (inglizcha)
   teglar: suv, faktlar, tabiat

   Matn shu yerdan boshlanadi. ...
   ```
2. Ishga tushirish:
   ```bash
   python -m ytstudio tayyorla
   ```
   ```bash
   python -m ytstudio xizmat
   ```
   `tayyorla` — bir marta; `xizmat` — to'xtovsiz, har 12 soatda. Boshqa buyruqlar: `ishla`, `yukla`, `holat`.
3. Natija: `chiqish/<fayl nomi>/rils_1..5.mp4`, `video_1..3.mp4`. Ishlangan matn `matn/tayyor/` ga o'tadi.

`matn/` bo'sh bo'lsa dastur hech narsa yasamaydi (o'zi matn to'qimaydi).

## Matn qanday bo'linadi

- **3 qisqa video**: matn 3 ta taxminan teng qismga bo'linadi — birgalikda **to'liq matn**.
- **5 rils**: matn 5 qismga bo'linadi; har rils o'z qismining boshidan ≤ 58 soniyaga sig'adigan gaplarni oladi.
  Gap o'rtasidan kesilmaydi; sig'magan gaplar shu rilsga kirmaydi (ular qisqa videolarda bor).
- 5 rils to'liq chiqishi uchun matnda kamida 5 gap bo'lsin; har rils ~45–55 s bo'lishi uchun
  matn taxminan 550–700 so'z bo'lgani ma'qul. Qisqa matnda rilslar ham qisqa chiqadi.

## Muhim cheklovlar

- **YouTube API kvotasi.** Odatiy loyiha kvotasi kuniga 10 000 birlik; bitta video yuklash hujjat bo'yicha
  1 600 birlik edi → kuniga ~6 video. Sizga kuniga 16 ta kerak — Google'dan kvota oshirishni so'rash kerak
  (joriy narxni rasmiy hujjatdan tekshiring: developers.google.com/youtube/v3/determine_quota_cost).
- **Tekshirilmagan API loyihasi.** 2020-yil 28-iyuldan keyin yaratilgan, Google auditidan o'tmagan loyiha
  orqali yuklangan videolar **majburan «private» (yopiq)** bo'lib qoladi. Hammaga ochiq yuklash uchun
  YouTube API Services auditidan o'tish kerak (bepul, lekin vaqt oladi).
- **Kanal chegarasi.** YouTube kanalga kunlik yuklash sonini ham cheklaydi (aniq son e'lon qilinmagan).
- **Kontent siyosati.** Bir xil qolipdagi ommaviy videolar YouTube'ning «takroriy kontent» siyosatiga tushishi va
  monetizatsiyadan chetlatilishi mumkin. Bu dastur hal qila olmaydigan xavf.
- **Ovoz** — Microsoft Edge onlayn xizmati (norasmiy kutubxona): bepul, lekin Microsoft o'zgartirsa
  ishlamay qolishi mumkin. Subtitr vaqti gap darajasida aniq, gap ichida taxminiy.
- **Fon** matn mazmuniga emas, siz yozgan `kalit:` so'zlariga mos tanlanadi.

## Sinov

```bash
python test_ytstudio.py
```
Internet va kalitlarsiz ishlaydi (ovozsiz rejim + gradient fon), ~30 soniya.

# 🚖 Haydovchilar E'lon Yuborish Boti (Driver Advertisement Bot)

Telegram guruhlariga haydovchi e'lonlarini avtomatik va muntazam ravishda
yuboradigan, to'liq production-ready Telegram bot. Bot faqat o'zi
administrator bo'lgan guruhlarga xabar yuboradi.

**Stack:** Python 3.13 · Aiogram 3.x · PostgreSQL · SQLAlchemy 2.x (async) ·
Alembic · Redis (FSM storage) · Docker.

---

## 📁 Loyiha tuzilishi

```
driver_ads_bot/
├── main.py                     # Kirish nuqtasi
├── bot/
│   ├── config.py                # Markazlashtirilgan konfiguratsiya (pydantic-settings)
│   ├── core/                    # Logging, DI konteyner, fon jarayonlar
│   ├── database/                # Async SQLAlchemy engine/session
│   ├── models/                  # ORM modellari (User, Payment, Advertisement, Group, AdminSetting)
│   ├── repositories/            # Repository Pattern — barcha SQL so'rovlar
│   ├── services/                # Biznes-logika qatlami
│   ├── scheduler/                # E'lon yuborish dvigateli (engine/manager/recovery)
│   ├── middlewares/              # DB session, throttling, banned-user
│   ├── filters/                  # IsAdmin filter
│   ├── states/                   # Aiogram FSM holatlari
│   ├── keyboards/                # Inline/Reply klaviaturalar
│   ├── handlers/
│   │   ├── user/                 # /start, to'lov, telefon, asosiy menyu, e'lon
│   │   ├── admin/                # Admin panel bo'limlari
│   │   └── group_events.py       # Guruh a'zolik holatini kuzatish
│   ├── utils/                    # Telefon normalizatsiya, matnlar, formatlash
│   └── exceptions/               # Maxsus xatoliklar
├── alembic/                      # DB migratsiyalari
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## ⚙️ Muhit o'zgaruvchilari (Environment Variables)

`.env.example` faylini `.env` ga nusxalab, qiymatlarni to'ldiring:

```bash
cp .env.example .env
```

| O'zgaruvchi | Tavsif |
|---|---|
| `BOT_TOKEN` | @BotFather'dan olingan bot tokeni |
| `ADMIN_IDS` | Admin panelga kira oladigan Telegram ID'lar (vergul bilan) |
| `ADMIN_NAME`, `ADMIN_PHONE`, `ADMIN_PROFILE_URL` | "Admin bilan bog'lanish" bo'limida ko'rsatiladi |
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@host:5432/dbname` |
| `REDIS_URL` | FSM holatlarini saqlash uchun (restart'dan keyin ham yo'qolmasligi uchun) |
| `TARIFFS_JSON` | Tariflar (JSON): key -> {label, days (null=umrbod), price} |
| `PAYMENT_CARD_NUMBER/OWNER/PHONE` | Chek orqali to'lov uchun karta ma'lumotlari |
| `AD_INTERVALS` | Ruxsat etilgan intervallar (daqiqa), masalan `5,10,15,20` |
| `AD_AUTO_STOP_HOURS` | E'lon avtomatik to'xtaydigan vaqt (soat), standart `24` |
| `SEND_CONCURRENCY_LIMIT` | Bir vaqtda nechta guruhga parallel yuborish mumkin |
| `GROUP_VALIDATION_INTERVAL_HOURS` | Guruhlarni qayta tekshirish oralig'i |

To'liq ro'yxat uchun `.env.example` faylига qarang.

---

## 🖥️ Lokal ishga tushirish (Docker'siz)

1. **PostgreSQL va Redis o'rnatilgan bo'lishi kerak** (lokal yoki masofaviy).

2. Virtual muhit yarating va kutubxonalarni o'rnating:

```bash
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. `.env` faylini to'ldiring (yuqoridagi jadvalga qarang).

4. Ma'lumotlar bazasi migratsiyalarini bajaring:

```bash
alembic upgrade head
```

5. Botni ishga tushiring:

```bash
python main.py
```

---

## 🐳 Docker bilan ishga tushirish (tavsiya etiladi)

```bash
cp .env.example .env
# .env faylini to'ldiring

docker compose up -d --build
```

Bu buyruq quyidagilarni avtomatik bajaradi:
1. PostgreSQL va Redis konteynerlarini ishga tushiradi (health-check bilan).
2. `migrate` konteyneri orqali `alembic upgrade head` ni bajaradi.
3. Faqat migratsiya muvaffaqiyatli tugagandan so'ng `bot` konteynerini ishga tushiradi.

Loglarni kuzatish:

```bash
docker compose logs -f bot
```

Botni to'xtatish:

```bash
docker compose down
```

Ma'lumotlar bazasini ham o'chirish (ehtiyot bo'ling — barcha ma'lumotlar yo'qoladi):

```bash
docker compose down -v
```

---

## 🗄️ Ma'lumotlar bazasi migratsiyalari

Yangi migratsiya yaratish (modellarga o'zgarish kiritgandan so'ng):

```bash
alembic revision --autogenerate -m "tavsif"
alembic upgrade head
```

Migratsiyani orqaga qaytarish:

```bash
alembic downgrade -1
```

---

## 🚀 Deploy (production)

1. Serverga loyihani ko'chiring (`git clone` yoki `scp`).
2. `.env` faylini production qiymatlar bilan to'ldiring (kuchli parollar, real `BOT_TOKEN`).
3. `docker compose up -d --build` orqali ishga tushiring.
4. Bot ishga tushganda avtomatik ravishda:
   - Bazadagi barcha `ACTIVE`/`PAUSED` e'lonlarni tiklaydi (restart recovery),
   - Guruhlarni davriy tekshiruvchi fon jarayonni,
   - Obuna muddatini kuzatuvchi fon jarayonni ishga tushiradi.
5. Server qayta yuklansa ham (`restart: unless-stopped`), Docker konteynerlar
   avtomatik qayta ishga tushadi va bot o'z holatini bazadan tiklaydi.

**Zaxira nusxa (backup):** `postgres_data` Docker volume'ini muntazam
zaxiralashni unutmang, masalan:

```bash
docker exec driver_ads_postgres pg_dump -U bot_user driver_ads_bot > backup.sql
```

---

## 🩺 Nosozliklarni bartaraf etish (Troubleshooting)

| Muammo | Yechim |
|---|---|
| Bot ishga tushmayapti, `BOT_TOKEN` xatoligi | `.env` dagi tokenni @BotFather'dan qayta tekshiring |
| `sqlalchemy.exc.OperationalError` | `DATABASE_URL` to'g'riligini va Postgres konteyneri ishlab turganini tekshiring |
| FSM holatlari restart'dan keyin yo'qolyapti | `REDIS_URL` to'g'ri sozlanganini va Redis konteyneri ishlashini tekshiring |
| Guruhga xabar yuborilmayapti | Botni guruhda administrator qilganingizni va guruh admin panelda "🟢 Aktiv" ekanligini tekshiring |
| `Bot ushbu guruhda administrator emas` | Guruh sozlamalarida botga admin huquqi bering, so'ng qaytadan `➕ Guruh qo'shish` orqali qo'shing |
| Migratsiya xatoligi | `docker compose logs migrate` orqali xato sababini ko'ring, keyin `docker compose up -d --build` ni qayta ishga tushiring |
| Ko'p FloodWait xatoliklari | `.env` dagi `SEND_CONCURRENCY_LIMIT` qiymatini pasaytiring |
| Loglarni ko'rish | `logs/` papkasidagi `bot.log`, `scheduler.log`, `payment.log`, `admin.log`, `errors.log` fayllariga qarang |

---

## 🔐 Xavfsizlik eslatmalari

- `.env` faylini hech qachon git repositoryga qo'shmang (`.gitignore` da allaqachon istisno qilingan).
- `ADMIN_IDS` ro'yxatini faqat ishonchli Telegram ID'lar bilan cheklang.
- Production muhitida PostgreSQL va Redis'ga tashqi tarmoqdan to'g'ridan-to'g'ri
  kirish imkoniyatini yoping (faqat ichki Docker tarmog'i orqali ulanish).

---

## 📜 Litsenziya

Ushbu loyiha buyurtma asosida ishlab chiqilgan va xususiy foydalanish uchun mo'ljallangan.

# 🤖 SetUp_tool.bot - Telegram Kalit So'z Izlovchi Bot

Bu bot izlovchi guruhlardagi kalit so'zlarni topib, shaxsiy guruhingizga xabar yuboradi.

---

## 📋 Xususiyatlar

✅ **Super Admin panel** - adminlar boshqaruvi  
✅ **Admin panel** - kalit so'zlar va guruhlar  
✅ **Kalit so'z izlash** - Userbot orqali real-time monitoring  
✅ **Shaxsiy guruh** - topilgan xabarlar yuboriladi  
✅ **Izlovchi guruhlar** - kalit so'z izlanadigan guruhlar  
✅ **Kundalik restart** - Userbotni avtomatik boshqarish  
✅ **Database** - barcha ma'lumotlar xavfsiz saqlanadi  

---

## 🚀 O'rnatish va Ishga Tushirish

### 1️⃣ **Kutubxonalarni o'rnatish**

```bash
pip install -r requirements.txt
```

### 2️⃣ **.env faylini sozlash**

`.env` faylini oching va o'z ma'lumotlaringizni kiriting:

```env
BOT_TOKEN=sizning_bot_tokeningiz
SUPER_ADMIN_ID=sizning_telegram_id
API_ID=sizning_api_id
API_HASH=sizning_api_hash
PHONE_NUMBER=+998901234567
SESSION_STRING=
```

⚠️ **SESSION_STRING** ni hozircha bo'sh qoldiring!

---

### 3️⃣ **Session String Yaratish**

Session yaratish uchun quyidagi buyruqni ishga tushiring:

```bash
python session_creator.py
```

Telefon raqamingizga SMS keladi:
1. SMS kodini kiriting
2. Agar 2FA (ikki bosqichli tasdiqlash) yoqilgan bo'lsa, parolni kiriting
3. Session string yaratiladi

**Session stringni ko'chiring** va `.env` faylidagi `SESSION_STRING=` qatoriga qo'ying.

---

### 4️⃣ **Botni Ishga Tushirish**

Botni ishga tushirish uchun:

```bash
python bot.py
```

Bot ishga tushdi! ✅

---

### 5️⃣ **Userbotni Ishga Tushirish**

**Yangi terminal** ochib, Userbotni ishga tushiring:

```bash
python userbot.py
```

Userbot ishga tushdi! ✅

---

## 📖 Foydalanish Bo'yicha Qo'llanma

### 🔐 **Super Admin**

1. Botga `/start` yuboring
2. Menyu ochiladi:
   - ➕ **Admin qo'shish** - Yangi admin qo'shish
   - 📋 **Adminlar ro'yxati** - Barcha adminlar
   - 🗑 **Admin o'chirish** - Adminni o'chirish
   - 🚪 **Admin xonasi** - Admin xonasiga kirish
   - 🔧 **Userbot sozlamalari** - Kundalik restart
   - 🤖 **Userbot holati** - Statistika va tekshiruv

---

### 👤 **Admin**

1. Botga `/start` yuboring
2. Admin menyusi ochiladi:
   - ➕ **Kalit so'z** - Yangi kalit so'z qo'shish
   - 📋 **Ko'rish** - Barcha kalit so'zlar
   - 🗑 **O'chirish** - Kalit so'zni o'chirish
   - ➕ **Shaxsiy guruh** - Xabarlar keladi
   - ➕ **Izlovchi guruh** - Kalit so'z izlanadi

---

## ⚙️ Userbot Sozlamalari

### Kundalik restart

Userbot har kuni ma'lum vaqtda to'xtatiladi va qayta ishga tushadi.

**Vaqtni o'zgartirish:**

Super Admin → Userbot sozlamalari → Vaqt yuboring:

```
00:00:02:00
```

- `00:00` - To'xtatish vaqti (soat:daqiqa)
- `02:00` - Ishga tushirish vaqti

**To'xtatishni o'chirish:**

```
off
```

Userbot 24/7 ishlaydi.

---

## 🔧 Guruh ID Olish

1. Botni guruhga admin qiling
2. Guruhda `/id` yuboring
3. Bot guruh ID sini yuboradi
4. ID ni ko'chiring va botga yuboring

---

## 📊 Qanday Ishlaydi?

1. **Admin** kalit so'z va guruhlarni qo'shadi
2. **Userbot** izlovchi guruhlardagi xabarlarni kuzatadi
3. Kalit so'z topilganda **shaxsiy guruhga** xabar yuboriladi
4. Xabarda:
   - 📢 Guruh nomi
   - 👤 Foydalanuvchi ismi
   - 🆔 User ID
   - 🔑 Kalit so'z
   - 💬 To'liq xabar
   - 🔗 Profilga o'tish tugmasi

---

## ⚠️ Muhim Eslatmalar

### Xavfsizlik

🔒 `.env` faylini **HECH QACHON** GitHub ga yuklamang!  
🔒 `SESSION_STRING` ni **HECH KIMGA** bermang!  
🔒 Bot tokenni **MAXFIY** saqlang!

### Yangilash Tavsiyasi

📌 Loyihani ishlatgandan keyin **ALBATTA** barcha ma'lumotlarni yangilang:
1. Bot tokenni yangilang (@BotFather → /revoke)
2. API credentials yangilang (my.telegram.org)
3. Session stringni yangilang (session_creator.py)

---

## 🐛 Muammolarni Hal Qilish

### Bot ishlamayapti

1. `.env` faylni tekshiring
2. `python bot.py` buyrug'ini qayta ishlating
3. Log fayllarni ko'ring: `bot.log`

### Userbot ishlamayapti

1. `SESSION_STRING` to'g'ri ekanligini tekshiring
2. `python userbot.py` buyrug'ini qayta ishlating
3. Log fayllarni ko'ring: `userbot.log`

### Xabarlar kelmayapti

1. Botni guruhga **admin** qiling
2. Kalit so'z to'g'ri yozilganligini tekshiring (katta-kichik harf farqi yo'q)
3. Shaxsiy guruh to'g'ri qo'shilganligini tekshiring

---

## 📝 Fayl Strukturasi

```
SetUp_tool.bot/
├── .env                    # Maxfiy sozlamalar
├── .gitignore              # GitHub ignore
├── bot.py                  # Asosiy bot
├── userbot.py              # Userbot (kalit so'z izlovchi)
├── database.py             # Database boshqaruvi
├── session_creator.py      # Session yaratish
├── requirements.txt        # Kerakli kutubxonalar
├── README.md               # Yo'riqnoma
├── bot_database.db         # Database (avtomatik yaratiladi)
├── bot.log                 # Bot log (avtomatik yaratiladi)
└── userbot.log             # Userbot log (avtomatik yaratiladi)
```

---

## 📞 Yordam

Muammolar bo'lsa:
1. Log fayllarni tekshiring (`bot.log`, `userbot.log`)
2. `.env` faylni to'g'ri to'ldirilganligini tekshiring
3. Barcha kutubxonalar o'rnatilganligini tekshiring

---

## 📜 Litsenziya

Bu loyiha shaxsiy foydalanish uchun mo'ljallangan.

---

**🎉 Omad tilaymiz! Bot muvaffaqiyatli ishlashini tilaymiz!**

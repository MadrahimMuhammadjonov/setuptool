# ============================================
# session_creator.py - Session String Yaratish
# ============================================

import asyncio
import os
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession

# .env fayldan sozlamalarni yuklash
load_dotenv()

API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
PHONE = os.getenv('PHONE_NUMBER')

print("=" * 60)
print("🔐 SESSION STRING YARATISH")
print("=" * 60)
print()

if not API_ID or not API_HASH or not PHONE:
    print("❌ .env faylida API_ID, API_HASH yoki PHONE_NUMBER topilmadi!")
    print("💡 Avval .env faylini to'g'ri to'ldiring!")
    exit()

print(f"📱 Telefon: {PHONE}")
print(f"🆔 API ID: {API_ID}")
print()

async def main():
    """Session yaratish"""
    try:
        # Bo'sh session bilan client yaratish
        client = TelegramClient(StringSession(), API_ID, API_HASH)
        
        await client.start(phone=PHONE)
        
        print()
        print("✅ Telegram akkauntga muvaffaqiyatli ulandingiz!")
        print()
        
        # Session stringni olish
        session_string = client.session.save()
        
        print("=" * 60)
        print("🎉 SESSION STRING TAYYOR!")
        print("=" * 60)
        print()
        print("📋 SESSION STRING:")
        print()
        print(session_string)
        print()
        print("=" * 60)
        print()
        print("📝 NAVBATDAGI QADAMLAR:")
        print()
        print("1. Yuqoridagi SESSION_STRING ni ko'chirib oling")
        print("2. .env faylini oching")
        print("3. SESSION_STRING= qatoriga bu stringni qo'ying")
        print("4. Faylni saqlang")
        print("5. Endi userbot.py ni ishga tushirishingiz mumkin!")
        print()
        print("⚠️ MUHIM: Bu stringni hech kimga bermang!")
        print("Bu string orqali sizning Telegram akkauntingizga kirilishi mumkin!")
        print()
        
        await client.disconnect()
        
    except Exception as e:
        print(f"❌ Xato: {e}")
        print()
        print("💡 Iltimos, quyidagilarni tekshiring:")
        print("1. Internet ulanishingiz faol")
        print("2. API_ID va API_HASH to'g'ri")
        print("3. Telefon raqam to'g'ri formatda (+998...)")

if __name__ == '__main__':
    asyncio.run(main())

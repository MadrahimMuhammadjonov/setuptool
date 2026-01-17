# ============================================
# userbot.py - Telegram Userbot
# ============================================

import logging
import asyncio
import os
from datetime import datetime, time, timedelta
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
import database as db

# .env fayldan sozlamalarni yuklash
load_dotenv()

# Logging sozlash
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('userbot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# ==================== SOZLAMALAR ====================
BOT_TOKEN = os.getenv('BOT_TOKEN')
SUPER_ADMIN_ID = int(os.getenv('SUPER_ADMIN_ID'))
PHONE = os.getenv('PHONE_NUMBER')
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
SESSION_STRING = os.getenv('SESSION_STRING', '')

if not all([BOT_TOKEN, SUPER_ADMIN_ID, PHONE, API_ID, API_HASH]):
    raise ValueError("❌ .env faylida kerakli ma'lumotlar topilmadi!")

if not SESSION_STRING:
    logger.warning("⚠️ SESSION_STRING bo'sh! Avval session_creator.py ishlatib session yarating!")

bot_instance = None

# ==================== XABAR YUBORISH ====================
async def send_notification(private_group_id, group_name, username, user_id, keyword, msg_text):
    """Kalit so'z topilganda shaxsiy guruhga xabar yuborish"""
    global bot_instance
    
    try:
        if not bot_instance:
            bot_instance = Bot(token=BOT_TOKEN)
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("👤 Profil", url=f"tg://user?id={user_id}")]
        ])
        
        # Xabarni qisqartirish (500 belgidan ko'p bo'lsa)
        if len(msg_text) > 500:
            msg_text = msg_text[:500] + "..."
        
        message_text = (
            f"🔍 Kalit so'z topildi! (Userbot)\n\n"
            f"📢 Guruh: {group_name}\n"
            f"👤 Foydalanuvchi: {username}\n"
            f"🆔 User ID: {user_id}\n"
            f"🔑 Kalit so'z: {keyword}\n\n"
            f"💬 Xabar:\n{msg_text}"
        )
        
        await bot_instance.send_message(
            chat_id=private_group_id,
            text=message_text,
            reply_markup=keyboard
        )
        
        logger.info(f"✅ Xabar yuborildi: Guruh={group_name}, Keyword={keyword}")
        
    except TelegramError as e:
        logger.error(f"❌ Telegram xato: {e}")
    except Exception as e:
        logger.error(f"❌ Xabar yuborishda xato: {e}")

# ==================== USERBOT HANDLER ====================
async def message_handler(event):
    """Barcha xabarlarni handle qilish"""
    try:
        if not event.message or not event.message.text:
            return
        
        chat = await event.get_chat()
        
        # Faqat guruh xabarlarini qayta ishlash
        if not hasattr(chat, 'megagroup'):
            return
        
        if not chat.megagroup:
            return
        
        group_id = event.chat_id
        msg_text = event.message.text
        group_name = getattr(chat, 'title', 'Unknown')
        
        sender = await event.get_sender()
        if not sender:
            return
        
        user_id = sender.id
        username = sender.username if sender.username else (sender.first_name if sender.first_name else "Unknown")
        
        logger.info(f"📨 Xabar: Guruh={group_name} (ID: {group_id}), User={username}")
        
        # Kalit so'zlarni tekshirish
        matches = db.check_keywords_in_message(group_id, msg_text)
        
        if matches:
            logger.info(f"🔍 {len(matches)} ta kalit so'z topildi!")
            
            for match in matches:
                try:
                    if match['private_group_id']:
                        await send_notification(
                            match['private_group_id'],
                            group_name,
                            username,
                            user_id,
                            match['keyword'],
                            msg_text
                        )
                except Exception as e:
                    logger.error(f"❌ Match handle qilishda xato: {e}")
        
    except Exception as e:
        logger.error(f"❌ Message handler xatosi: {e}")

# ==================== USERBOT ISHGA TUSHIRISH ====================
async def start_userbot():
    """Userbot ishga tushirish"""
    try:
        db.init_db()
        logger.info("✅ Database initialized")
        
        if not SESSION_STRING:
            logger.error("❌ SESSION_STRING topilmadi! session_creator.py ishlatib session yarating!")
            return
        
        client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
        
        await client.start(phone=PHONE)
        logger.info("✅ Userbot ulanmoqda...")
        
        me = await client.get_me()
        logger.info(f"✅ Userbot ishga tushdi: {me.first_name} (@{me.username})")
        
        @client.on(events.NewMessage())
        async def handler(event):
            await message_handler(event)
        
        logger.info("✅ Message handler qo'shildi")
        logger.info("🎯 Userbot barcha xabarlarni kuzatyapti...")
        
        await client.run_until_disconnected()
        
    except Exception as e:
        logger.error(f"❌ Userbot ishga tushirishda xato: {e}")
        raise

# ==================== KUNDALIK RESTART ====================
async def start_with_schedule():
    """Userbot kundalik restart bilan ishga tushirish"""
    
    while True:
        try:
            logger.info("🚀 Userbot ishga tushmoqda...")
            
            schedule_enabled = db.get_setting('userbot_schedule_enabled', 'true')
            
            if schedule_enabled != 'true':
                logger.info("⏰ Kundalik restart o'chirilgan. 24/7 ishlamoqda...")
                await start_userbot()
                continue
            
            stop_time_str = db.get_setting('userbot_stop_time', '00:00')
            start_time_str = db.get_setting('userbot_start_time', '02:00')
            
            stop_h, stop_m = map(int, stop_time_str.split(':'))
            start_h, start_m = map(int, start_time_str.split(':'))
            
            now = datetime.now()
            
            stop_today = datetime.combine(now.date(), time(stop_h, stop_m))
            if now >= stop_today:
                stop_today = datetime.combine(now.date() + timedelta(days=1), time(stop_h, stop_m))
            
            seconds_until_stop = (stop_today - now).total_seconds()
            
            hours = int(seconds_until_stop / 3600)
            minutes = int((seconds_until_stop % 3600) / 60)
            logger.info(f"⏰ Userbot {stop_time_str} da to'xtatiladi ({hours} soat {minutes} daqiqa)")
            
            try:
                await asyncio.wait_for(start_userbot(), timeout=seconds_until_stop)
            except asyncio.TimeoutError:
                logger.info(f"🌙 Soat {stop_time_str} - Userbot to'xtatilmoqda...")
            
            start_tomorrow = datetime.combine(now.date() + timedelta(days=1), time(start_h, start_m))
            sleep_seconds = (start_tomorrow - datetime.now()).total_seconds()
            
            sleep_hours = int(sleep_seconds / 3600)
            sleep_minutes = int((sleep_seconds % 3600) / 60)
            logger.info(f"💤 {sleep_hours} soat {sleep_minutes} daqiqa kutish ({stop_time_str} - {start_time_str})...")
            await asyncio.sleep(sleep_seconds)
            
            logger.info(f"🌅 Soat {start_time_str} - Qayta ishga tushirish...")
            
        except Exception as e:
            logger.error(f"❌ Xato: {e}")
            logger.info("⏳ 5 daqiqadan keyin qayta urinish...")
            await asyncio.sleep(300)

# ==================== MAIN ====================
async def main():
    """Asosiy funksiya"""
    logger.info("=" * 60)
    logger.info("🤖 USERBOT ISHGA TUSHMOQDA")
    logger.info("=" * 60)
    
    db.init_db()
    
    schedule_enabled = db.get_setting('userbot_schedule_enabled', 'true')
    
    if schedule_enabled == 'true':
        logger.info("⏰ Kundalik restart rejimi yoqilgan")
        await start_with_schedule()
    else:
        logger.info("⏰ Kundalik restart o'chirilgan. 24/7 ishlash rejimi")
        await start_userbot()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⛔ Userbot to'xtatildi (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ Fatal xato: {e}")
        import traceback
        traceback.print_exc()

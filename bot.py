# ============================================
# bot.py - Telegram Bot (Railway uchun tuzatilgan)
# ============================================

import logging
import os
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import database as db

# .env fayldan sozlamalarni yuklash
load_dotenv()

# Logging sozlash
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# ==================== SOZLAMALAR ====================
TOKEN = os.getenv('BOT_TOKEN')
SUPER_ADMIN_ID = int(os.getenv('SUPER_ADMIN_ID'))

if not TOKEN or not SUPER_ADMIN_ID:
    raise ValueError("❌ .env faylida BOT_TOKEN yoki SUPER_ADMIN_ID topilmadi!")

# ==================== KEYBOARD ====================

def super_admin_keyboard():
    """Super admin menyusi"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Yangi admin qo'shish", callback_data='add_admin')],
        [InlineKeyboardButton("📋 Adminlar ro'yxati", callback_data='list_admins')],
        [InlineKeyboardButton("🗑 Admin o'chirish", callback_data='remove_admin')],
        [InlineKeyboardButton("🚪 Admin xonasiga o'tish", callback_data='enter_admin_room')],
        [InlineKeyboardButton("🔧 Userbot sozlamalari", callback_data='userbot_settings')],
        [InlineKeyboardButton("🤖 Userbotni tekshirish", callback_data='check_userbot')]
    ])

def admin_keyboard():
    """Admin menyusi"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Kalit so'z", callback_data='add_keyword'), 
         InlineKeyboardButton("📋 Ko'rish", callback_data='view_keywords')],
        [InlineKeyboardButton("🗑 So'z o'chirish", callback_data='delete_keyword')],
        [InlineKeyboardButton("➕ Shaxsiy guruh", callback_data='add_private_group')],
        [InlineKeyboardButton("👁 Ko'rish", callback_data='view_private_group'), 
         InlineKeyboardButton("🗑 O'chirish", callback_data='delete_private_group')],
        [InlineKeyboardButton("➕ Izlovchi guruh", callback_data='add_search_group')],
        [InlineKeyboardButton("📋 Ko'rish", callback_data='view_search_groups'), 
         InlineKeyboardButton("🗑 O'chirish", callback_data='delete_search_group')]
    ])

def back_button():
    """Ortga qaytish tugmasi"""
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data='back_to_main')]])

# ==================== HANDLERS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
    if user_id == SUPER_ADMIN_ID:
        await update.message.reply_text(
            "🔐 Assalomu alaykum, Super Admin!\n\n"
            "Bu bot izlovchi guruhlardagi kalit so'zlarni topib, shaxsiy guruhingizga yuboradi.\n\n"
            "Menyudan kerakli bo'limni tanlang:",
            reply_markup=super_admin_keyboard()
        )
    elif db.is_admin(user_id, SUPER_ADMIN_ID):
        await update.message.reply_text(
            f"👋 Assalomu alaykum, {username}!\n\n"
            f"🏠 Shaxsiy xonangizga xush kelibsiz.\n"
            f"Bu yerda kalit so'zlar va guruhlarni boshqarishingiz mumkin:",
            reply_markup=admin_keyboard()
        )
    else:
        keyboard = [[InlineKeyboardButton("👤 Adminga bog'lanish", url=f"tg://user?id={SUPER_ADMIN_ID}")]]
        await update.message.reply_text(
            f"👋 Assalomu alaykum, {username}!\n\n"
            f"ℹ️ Bu bot izlovchi guruhlardagi kalit so'zlarni topib, "
            f"adminlarga xabar yuborish uchun mo'ljallangan.\n\n"
            f"⚠️ Botdan faqat adminlar foydalana oladi!\n"
            f"Botdan foydalanish uchun adminga murojaat qiling.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Guruh ID olish (/id buyrug'i)"""
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    chat_title = update.effective_chat.title if hasattr(update.effective_chat, 'title') else "Shaxsiy chat"
    
    await update.message.reply_text(
        f"📊 Chat ma'lumotlari:\n\n"
        f"📝 Nomi: {chat_title}\n"
        f"🆔 ID: `{chat_id}`\n"
        f"📁 Turi: {chat_type}",
        parse_mode='Markdown'
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inline button callback handler"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    # ========== SUPER ADMIN FUNKSIYALARI ==========
    
    if data == 'add_admin' and user_id == SUPER_ADMIN_ID:
        context.user_data['waiting'] = 'admin_id'
        await query.edit_message_text(
            "📝 Yangi admin ID raqamini yuboring:\n\n"
            "💡 ID olish: @userinfobot ga /start yuboring",
            reply_markup=back_button()
        )

    elif data == 'list_admins' and user_id == SUPER_ADMIN_ID:
        admins = db.get_all_admins()
        if admins:
            keyboard = [[InlineKeyboardButton(f"👤 {u} (ID: {i})", url=f"tg://user?id={i}")] for i, u in admins]
            keyboard.append([InlineKeyboardButton("⬅️ Ortga", callback_data='back_to_main')])
            await query.edit_message_text(
                f"📋 Adminlar ro'yxati ({len(admins)} ta):",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.edit_message_text("ℹ️ Hozircha adminlar yo'q.", reply_markup=back_button())

    elif data == 'remove_admin' and user_id == SUPER_ADMIN_ID:
        admins = db.get_all_admins()
        if admins:
            keyboard = [[InlineKeyboardButton(f"🗑 {u}", callback_data=f'rmadm_{i}')] for i, u in admins]
            keyboard.append([InlineKeyboardButton("⬅️ Ortga", callback_data='back_to_main')])
            await query.edit_message_text(
                "🗑 O'chirish uchun adminni tanlang:\n\n"
                "⚠️ Admin o'chirilganda uning barcha ma'lumotlari (kalit so'zlar, guruhlar) ham o'chiriladi!",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.edit_message_text("ℹ️ O'chiriladigan adminlar yo'q.", reply_markup=back_button())

    elif data.startswith('rmadm_') and user_id == SUPER_ADMIN_ID:
        admin_id = int(data.split('_')[1])
        db.remove_admin(admin_id)
        await query.edit_message_text(
            "✅ Admin va uning barcha ma'lumotlari o'chirildi!",
            reply_markup=back_button()
        )

    elif data == 'enter_admin_room' and user_id == SUPER_ADMIN_ID:
        admins = db.get_all_admins()
        if admins:
            keyboard = [[InlineKeyboardButton(f"🚪 {u}", callback_data=f'enter_{i}')] for i, u in admins]
            keyboard.append([InlineKeyboardButton("⬅️ Ortga", callback_data='back_to_main')])
            await query.edit_message_text(
                "🚪 Qaysi admin xonasiga kirmoqchisiz?",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.edit_message_text("ℹ️ Adminlar yo'q.", reply_markup=back_button())

    elif data.startswith('enter_') and user_id == SUPER_ADMIN_ID:
        admin_id = int(data.split('_')[1])
        context.user_data['viewing_admin'] = admin_id
        await query.edit_message_text(
            f"🏠 Admin xonasi (ID: {admin_id}):\n\n"
            f"Ushbu xonada barcha admin funksiyalaridan foydalanishingiz mumkin.",
            reply_markup=admin_keyboard()
        )

    elif data == 'userbot_settings' and user_id == SUPER_ADMIN_ID:
        stop_time = db.get_setting('userbot_stop_time', '00:00')
        start_time = db.get_setting('userbot_start_time', '02:00')
        schedule_enabled = db.get_setting('userbot_schedule_enabled', 'true')
        
        status = "✅ Yoqilgan" if schedule_enabled == 'true' else "❌ O'chirilgan"
        
        text = f"⚙️ Userbot sozlamalari:\n\n⏰ Kundalik to'xtatish: {status}\n"
        
        if schedule_enabled == 'true':
            text += f"🌙 To'xtatish vaqti: {stop_time}\n🌅 Ishga tushirish vaqti: {start_time}\n\n"
        else:
            text += "\n"
        
        text += "💡 Vaqtni o'zgartirish uchun quyidagi formatda yuboring:\n"
        text += "<code>00:00:02:00</code>\n(00:00 da to'xtatadi, 02:00 da ishga tushiradi)\n\n"
        text += "📝 To'xtatishni o'chirish uchun: <code>off</code>"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ To'xtatishni o'chirish", callback_data='userbot_disable_schedule')],
            [InlineKeyboardButton("⬅️ Ortga", callback_data='back_to_main')]
        ])
        
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='HTML')
        context.user_data['waiting'] = 'userbot_time'

    elif data == 'userbot_disable_schedule' and user_id == SUPER_ADMIN_ID:
        db.set_setting('userbot_schedule_enabled', 'false')
        await query.edit_message_text(
            "✅ Userbot to'xtatish o'chirildi!\n\n"
            "🤖 Userbot endi 24/7 ishlaydi.",
            reply_markup=back_button()
        )
        context.user_data.pop('waiting', None)

    elif data == 'check_userbot' and user_id == SUPER_ADMIN_ID:
        try:
            conn = db.get_db()
            c = conn.cursor()
            
            c.execute("SELECT COUNT(*) as cnt FROM admins")
            admin_count = c.fetchone()['cnt']
            
            c.execute("SELECT COUNT(*) as cnt FROM keywords")
            keyword_count = c.fetchone()['cnt']
            
            c.execute("SELECT COUNT(*) as cnt FROM search_groups")
            search_group_count = c.fetchone()['cnt']
            
            c.execute("SELECT COUNT(*) as cnt FROM private_groups")
            private_group_count = c.fetchone()['cnt']
            
            last_check = db.get_setting('userbot_last_check', 'Hech qachon')
            schedule_enabled = db.get_setting('userbot_schedule_enabled', 'true')
            stop_time = db.get_setting('userbot_stop_time', '00:00')
            start_time = db.get_setting('userbot_start_time', '02:00')
            
            conn.close()
            
            text = f"🤖 Userbot holati:\n\n📊 Statistika:\n"
            text += f"👥 Adminlar: {admin_count} ta\n"
            text += f"🔑 Kalit so'zlar: {keyword_count} ta\n"
            text += f"🔍 Izlovchi guruhlar: {search_group_count} ta\n"
            text += f"📤 Shaxsiy guruhlar: {private_group_count} ta\n\n"
            text += f"⏰ Oxirgi tekshiruv: {last_check}\n"
            text += f"⚙️ Reja: {schedule_enabled} ({stop_time}-{start_time})"
            
            await query.edit_message_text(text, reply_markup=back_button())
        except Exception as e:
            await query.edit_message_text(f"❌ Xato: {e}", reply_markup=back_button())

    # ========== ADMIN FUNKSIYALARI ==========
    
    elif data == 'back_to_main':
        context.user_data.pop('waiting', None)
        context.user_data.pop('viewing_admin', None)
        if user_id == SUPER_ADMIN_ID:
            await query.edit_message_text(
                "🔐 Super Admin menyusi:",
                reply_markup=super_admin_keyboard()
            )
        else:
            await query.edit_message_text(
                "🏠 Admin menyusi:",
                reply_markup=admin_keyboard()
            )

    elif data == 'add_keyword':
        context.user_data['waiting'] = 'keyword'
        await query.edit_message_text(
            "📝 Yangi kalit so'zni yuboring:\n\n"
            "💡 Bir nechta bo'lsa, vergul bilan ajrating.\n"
            "Masalan: <code>ish, vakansiya, usta</code>",
            reply_markup=back_button(),
            parse_mode='HTML'
        )

    elif data == 'view_keywords':
        admin_id = context.user_data.get('viewing_admin', user_id)
        keywords = db.get_admin_keywords(admin_id)
        if keywords:
            text = "📋 Sizning kalit so'zlaringiz:\n\n"
            for i, k in enumerate(keywords, 1):
                text += f"{i}. {k}\n"
            await query.edit_message_text(text, reply_markup=back_button())
        else:
            await query.edit_message_text("ℹ️ Kalit so'zlar topilmadi.", reply_markup=back_button())

    elif data == 'delete_keyword':
        admin_id = context.user_data.get('viewing_admin', user_id)
        keywords = db.get_admin_keywords(admin_id)
        if keywords:
            keyboard = [[InlineKeyboardButton(f"🗑 {k}", callback_data=f'delkey_{k}')] for k in keywords]
            keyboard.append([InlineKeyboardButton("⬅️ Ortga", callback_data='back_to_main')])
            await query.edit_message_text(
                "🗑 O'chirish uchun kalit so'zni tanlang:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.edit_message_text("ℹ️ O'chiriladigan kalit so'zlar yo'q.", reply_markup=back_button())

    elif data.startswith('delkey_'):
        admin_id = context.user_data.get('viewing_admin', user_id)
        keyword = data.replace('delkey_', '')
        db.remove_keyword(admin_id, keyword)
        await query.edit_message_text(f"✅ '{keyword}' o'chirildi!", reply_markup=back_button())

    elif data == 'add_private_group':
        context.user_data['waiting'] = 'private_group'
        await query.edit_message_text(
            "📝 Shaxsiy guruh ID raqamini yoki linkini yuboring:\n\n"
            "💡 ID olish uchun guruhda /id buyrug'ini bering.",
            reply_markup=back_button()
        )

    elif data == 'view_private_group':
        admin_id = context.user_data.get('viewing_admin', user_id)
        groups = db.get_admin_private_groups(admin_id)
        if groups:
            text = "👁 Shaxsiy guruhlaringiz:\n\n"
            for i, (gid, gname, glink) in enumerate(groups, 1):
                text += f"{i}. {gname} (ID: {gid})\n"
            await query.edit_message_text(text, reply_markup=back_button())
        else:
            await query.edit_message_text("ℹ️ Shaxsiy guruhlar topilmadi.", reply_markup=back_button())

    elif data == 'delete_private_group':
        admin_id = context.user_data.get('viewing_admin', user_id)
        groups = db.get_admin_private_groups(admin_id)
        if groups:
            keyboard = [[InlineKeyboardButton(f"🗑 {name}", callback_data=f'delpriv_{gid}')] for gid, name, link in groups]
            keyboard.append([InlineKeyboardButton("⬅️ Ortga", callback_data='back_to_main')])
            await query.edit_message_text(
                "🗑 O'chirish uchun guruhni tanlang:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.edit_message_text("ℹ️ O'chiriladigan guruhlar yo'q.", reply_markup=back_button())

    elif data.startswith('delpriv_'):
        admin_id = context.user_data.get('viewing_admin', user_id)
        group_id = data.split('_')[1]
        db.remove_private_group(admin_id, group_id)
        await query.edit_message_text("✅ Shaxsiy guruh o'chirildi!", reply_markup=back_button())

    elif data == 'add_search_group':
        context.user_data['waiting'] = 'search_group'
        await query.edit_message_text(
            "📝 Izlovchi guruh ID raqamini yoki linkini yuboring:\n\n"
            "💡 Bot ushbu guruhdagi xabarlarni kuzatadi.",
            reply_markup=back_button()
        )

    elif data == 'view_search_groups':
        admin_id = context.user_data.get('viewing_admin', user_id)
        groups = db.get_admin_search_groups(admin_id)
        if groups:
            text = "📋 Izlovchi guruhlar:\n\n"
            for i, (gid, gname, glink) in enumerate(groups, 1):
                text += f"{i}. {gname} (ID: {gid})\n"
            await query.edit_message_text(text, reply_markup=back_button())
        else:
            await query.edit_message_text("ℹ️ Izlovchi guruhlar topilmadi.", reply_markup=back_button())

    elif data == 'delete_search_group':
        admin_id = context.user_data.get('viewing_admin', user_id)
        groups = db.get_admin_search_groups(admin_id)
        if groups:
            keyboard = [[InlineKeyboardButton(f"🗑 {name}", callback_data=f'delsrch_{gid}')] for gid, name, link in groups]
            keyboard.append([InlineKeyboardButton("⬅️ Ortga", callback_data='back_to_main')])
            await query.edit_message_text(
                "🗑 O'chirish uchun guruhni tanlang:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.edit_message_text("ℹ️ O'chiriladigan guruhlar yo'q.", reply_markup=back_button())

    elif data.startswith('delsrch_'):
        admin_id = context.user_data.get('viewing_admin', user_id)
        group_id = data.split('_')[1]
        db.remove_search_group(admin_id, group_id)
        await query.edit_message_text("✅ Izlovchi guruh o'chirildi!", reply_markup=back_button())

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Matnli xabarlarni qayta ishlash"""
    user_id = update.effective_user.id
    text = update.message.text
    waiting = context.user_data.get('waiting')

    if not waiting:
        return

    if waiting == 'admin_id' and user_id == SUPER_ADMIN_ID:
        try:
            new_admin_id = int(text)
            db.add_admin(new_admin_id, f"Admin_{new_admin_id}")
            await update.message.reply_text(
                f"✅ Yangi admin qo'shildi! (ID: {new_admin_id})",
                reply_markup=back_button()
            )
        except ValueError:
            await update.message.reply_text("❌ Noto'g'ri ID! Faqat raqam yuboring.")
        context.user_data.pop('waiting', None)

    elif waiting == 'userbot_time' and user_id == SUPER_ADMIN_ID:
        if text.lower() == 'off':
            db.set_setting('userbot_schedule_enabled', 'false')
            await update.message.reply_text("✅ Userbot to'xtatish o'chirildi!", reply_markup=back_button())
        else:
            try:
                parts = text.split(':')
                if len(parts) == 4:
                    stop = f"{parts[0]}:{parts[1]}"
                    start = f"{parts[2]}:{parts[3]}"
                    db.set_setting('userbot_stop_time', stop)
                    db.set_setting('userbot_start_time', start)
                    db.set_setting('userbot_schedule_enabled', 'true')
                    await update.message.reply_text(
                        f"✅ Vaqt o'rnatildi!\n🌙 To'xtash: {stop}\n🌅 Ishga tushish: {start}",
                        reply_markup=back_button()
                    )
                else:
                    await update.message.reply_text("❌ Format noto'g'ri! Masalan: 00:00:02:00")
            except:
                await update.message.reply_text("❌ Xato yuz berdi!")
        context.user_data.pop('waiting', None)

    elif waiting == 'keyword':
        admin_id = context.user_data.get('viewing_admin', user_id)
        keywords = [k.strip() for k in text.split(',') if k.strip()]
        for k in keywords:
            db.add_keyword(admin_id, k)
        await update.message.reply_text(
            f"✅ {len(keywords)} ta kalit so'z qo'shildi!",
            reply_markup=back_button()
        )
        context.user_data.pop('waiting', None)

    elif waiting == 'private_group':
        admin_id = context.user_data.get('viewing_admin', user_id)
        if text.startswith("http"):
            db.add_private_group(admin_id, group_link=text, group_name="Link orqali guruh")
            await update.message.reply_text(
                "✅ Shaxsiy guruh qo'shildi: Link orqali guruh",
                reply_markup=back_button()
            )
        else:
            try:
                gid = int(text)
                try:
                    chat = await context.bot.get_chat(gid)
                    gname = chat.title or f"Guruh {gid}"
                except:
                    gname = f"Guruh {gid}"
                db.add_private_group(admin_id, group_id=gid, group_name=gname)
                await update.message.reply_text(
                    f"✅ Shaxsiy guruh qo'shildi: {gname}",
                    reply_markup=back_button()
                )
            except:
                await update.message.reply_text(
                    "❌ Noto'g'ri ID yoki link!",
                    reply_markup=back_button()
                )
        context.user_data.pop('waiting', None)

    elif waiting == 'search_group':
        admin_id = context.user_data.get('viewing_admin', user_id)
        if text.startswith("http"):
            success, message = db.add_search_group(admin_id, SUPER_ADMIN_ID, group_link=text, group_name="Link orqali guruh")
            if success:
                await update.message.reply_text(
                    f"✅ {message}: Link orqali guruh",
                    reply_markup=back_button()
                )
            else:
                await update.message.reply_text(f"❌ {message}", reply_markup=back_button())
        else:
            try:
                gid = int(text)
                try:
                    chat = await context.bot.get_chat(gid)
                    gname = chat.title or f"Guruh {gid}"
                except:
                    gname = f"Guruh {gid}"
                
                success, message = db.add_search_group(admin_id, SUPER_ADMIN_ID, group_id=gid, group_name=gname)
                if success:
                    await update.message.reply_text(
                        f"✅ {message}: {gname}",
                        reply_markup=back_button()
                    )
                else:
                    await update.message.reply_text(f"❌ {message}", reply_markup=back_button())
            except:
                await update.message.reply_text(
                    "❌ Noto'g'ri ID yoki link!",
                    reply_markup=back_button()
                )
        context.user_data.pop('waiting', None)

async def check_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Guruh xabarlarini tekshirish (Bot orqali)"""
    if not update.message or not update.message.text:
        return
    
    chat_type = update.message.chat.type
    if chat_type not in ['group', 'supergroup']:
        return
    
    msg_text = update.message.text
    group_id = update.message.chat.id
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name or "Unknown"
    group_name = update.message.chat.title or "Unknown group"
    
    matches = db.check_keywords_in_message(group_id, msg_text)
    
    for match in matches:
        try:
            keyboard = [[InlineKeyboardButton("👤 Profil", url=f"tg://user?id={user_id}")]]
            if match['private_group_id']:
                await context.bot.send_message(
                    chat_id=match['private_group_id'],
                    text=(f"🔍 Kalit so'z topildi! (Bot)\n\n"
                          f"📢 Guruh: {group_name}\n"
                          f"👤 Foydalanuvchi: {username}\n"
                          f"🆔 User ID: {user_id}\n"
                          f"🔑 Kalit so'z: {match['keyword']}\n\n"
                          f"💬 Xabar:\n{msg_text}"),
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
        except Exception as e:
            logger.error(f"Bot xabar yuborishda xato: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xatolarni log qilish"""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Bot ishga tushirish"""
    logger.info("=" * 60)
    logger.info("🤖 BOT ISHGA TUSHMOQDA")
    logger.info("=" * 60)
    
    # Database yaratish
    db.init_db()
    
    # Default sozlamalarni o'rnatish
    if not db.get_setting('userbot_stop_time'):
        db.set_setting('userbot_stop_time', '00:00')
    if not db.get_setting('userbot_start_time'):
        db.set_setting('userbot_start_time', '02:00')
    if not db.get_setting('userbot_schedule_enabled'):
        db.set_setting('userbot_schedule_enabled', 'true')
    
    # Application yaratish (v20+ uchun)
    application = Application.builder().token(TOKEN).build()

    # Handlerlar
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("id", get_chat_id))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, handle_text))
    application.add_handler(MessageHandler(filters.TEXT & (filters.ChatType.GROUPS | filters.ChatType.SUPERGROUP), check_group_message))
    application.add_error_handler(error_handler)

    logger.info("🚀 Bot ishga tushmoqda...")
    
    try:
        logger.info("✅ Bot ishga tushdi!")
        logger.info(f"🔐 Super Admin ID: {SUPER_ADMIN_ID}")
        logger.info("💡 Botni to'xtatish uchun Ctrl+C bosing")
        application.run_polling()
    except KeyboardInterrupt:
        logger.info("\n⛔ Bot to'xtatildi (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ Xato: {e}")

if __name__ == '__main__':
    main()

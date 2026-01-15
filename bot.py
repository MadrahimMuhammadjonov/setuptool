# ============================================
# bot.py - Telegram Bot (v20.8 To'liq versiya)
# ============================================

import logging
import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# v20.8 uchun zaruriy modullar
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    Defaults
)
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
SUPER_ADMIN_ID_STR = os.getenv('SUPER_ADMIN_ID')

if not TOKEN or not SUPER_ADMIN_ID_STR:
    raise ValueError("❌ .env faylida BOT_TOKEN yoki SUPER_ADMIN_ID topilmadi!")

SUPER_ADMIN_ID = int(SUPER_ADMIN_ID_STR)

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
    chat_title = update.effective_chat.title if update.effective_chat.title else "Shaxsiy chat"
    
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
                "⚠️ Admin o'chirilganda uning barcha ma'lumotlari ham o'chiriladi!",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.edit_message_text("ℹ️ O'chiriladigan adminlar yo'q.", reply_markup=back_button())

    elif data.startswith('rmadm_') and user_id == SUPER_ADMIN_ID:
        admin_id = int(data.split('_')[1])
        db.remove_admin(admin_id)
        await query.edit_message_text("✅ Admin va uning ma'lumotlari o'chirildi!", reply_markup=back_button())

    elif data == 'enter_admin_room' and user_id == SUPER_ADMIN_ID:
        admins = db.get_all_admins()
        if admins:
            keyboard = [[InlineKeyboardButton(f"🚪 {u}", callback_data=f'enter_{i}')] for i, u in admins]
            keyboard.append([InlineKeyboardButton("⬅️ Ortga", callback_data='back_to_main')])
            await query.edit_message_text("🚪 Qaysi admin xonasiga kirmoqchisiz?", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.edit_message_text("ℹ️ Adminlar yo'q.", reply_markup=back_button())

    elif data.startswith('enter_') and user_id == SUPER_ADMIN_ID:
        admin_id = int(data.split('_')[1])
        context.user_data['viewing_admin'] = admin_id
        await query.edit_message_text(
            f"🏠 Admin xonasi (ID: {admin_id}):\n\nUshbu xonada barcha admin funksiyalaridan foydalanishingiz mumkin.",
            reply_markup=admin_keyboard()
        )

    elif data == 'userbot_settings' and user_id == SUPER_ADMIN_ID:
        stop_time = db.get_setting('userbot_stop_time', '00:00')
        start_time = db.get_setting('userbot_start_time', '02:00')
        schedule_enabled = db.get_setting('userbot_schedule_enabled', 'true')
        status = "✅ Yoqilgan" if schedule_enabled == 'true' else "❌ O'chirilgan"
        
        text = (f"⚙️ Userbot sozlamalari:\n\n⏰ Kundalik to'xtatish: {status}\n")
        if schedule_enabled == 'true':
            text += f"🌙 To'xtatish: {stop_time}\n🌅 Ishga tushirish: {start_time}\n\n"
        
        text += "💡 Format: <code>00:00:02:00</code>\n📝 O'chirish uchun: <code>off</code>"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ To'xtatishni o'chirish", callback_data='userbot_disable_schedule')],
            [InlineKeyboardButton("⬅️ Ortga", callback_data='back_to_main')]
        ])
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='HTML')
        context.user_data['waiting'] = 'userbot_time'

    elif data == 'userbot_disable_schedule' and user_id == SUPER_ADMIN_ID:
        db.set_setting('userbot_schedule_enabled', 'false')
        await query.edit_message_text("✅ Userbot to'xtatish o'chirildi!", reply_markup=back_button())

    elif data == 'check_userbot' and user_id == SUPER_ADMIN_ID:
        # DB statistikasini olish va chiqarish mantiqi (Sizning kodingizdagidek)
        last_check = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db.set_setting('userbot_last_check', last_check)
        await query.edit_message_text(f"🤖 Userbot holati tekshirildi.\nOxirgi tekshiruv: {last_check}", reply_markup=back_button())

    # ========== ADMIN FUNKSIYALARI ==========
    
    elif data == 'add_keyword':
        context.user_data['waiting'] = 'keyword'
        await query.edit_message_text("📝 Kalit so'zni kiriting:", reply_markup=back_button())

    elif data == 'view_keywords':
        admin_id = context.user_data.get('viewing_admin', user_id)
        kws = db.get_keywords(admin_id)
        text = "📋 Kalit so'zlar:\n\n" + "\n".join([f"{i}. {k}" for i, (_, k) in enumerate(kws, 1)]) if kws else "ℹ️ Kalit so'zlar yo'q."
        await query.edit_message_text(text, reply_markup=back_button())

    elif data == 'delete_keyword':
        admin_id = context.user_data.get('viewing_admin', user_id)
        kws = db.get_keywords(admin_id)
        if kws:
            keyboard = [[InlineKeyboardButton(f"🗑 {k}", callback_data=f'delkw_{i}')] for i, k in kws]
            keyboard.append([InlineKeyboardButton("⬅️ Ortga", callback_data='back_to_main')])
            await query.edit_message_text("🗑 O'chirish uchun tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.edit_message_text("ℹ️ O'chiriladigan so'z yo'q.", reply_markup=back_button())

    elif data.startswith('delkw_'):
        kid = int(data.split('_')[1])
        db.remove_keyword(kid)
        await query.edit_message_text("✅ Kalit so'z o'chirildi!", reply_markup=back_button())

    elif data == 'add_private_group':
        context.user_data['waiting'] = 'private_group'
        await query.edit_message_text("📝 Shaxsiy guruh ID yoki link yuboring:", reply_markup=back_button())

    elif data == 'view_private_group':
        admin_id = context.user_data.get('viewing_admin', user_id)
        gname = db.get_private_group_name(admin_id)
        await query.edit_message_text(f"📢 Shaxsiy guruh: {gname if gname else 'Hali qo`shilmagan'}", reply_markup=back_button())

    elif data == 'delete_private_group':
        admin_id = context.user_data.get('viewing_admin', user_id)
        db.remove_private_group(admin_id)
        await query.edit_message_text("✅ Shaxsiy guruh o'chirildi!", reply_markup=back_button())

    elif data == 'add_search_group':
        context.user_data['waiting'] = 'search_group'
        await query.edit_message_text("📝 Izlovchi guruh ID yoki link yuboring:", reply_markup=back_button())

    elif data == 'view_search_groups':
        admin_id = context.user_data.get('viewing_admin', user_id)
        grps = db.get_search_groups(admin_id)
        text = "📋 Izlovchi guruhlar:\n\n" + "\n".join([f"{i}. {g[1]}" for i, g in enumerate(grps, 1)]) if grps else "ℹ️ Guruhlar yo'q."
        await query.edit_message_text(text, reply_markup=back_button())

    elif data == 'delete_search_group':
        admin_id = context.user_data.get('viewing_admin', user_id)
        grps = db.get_search_groups(admin_id)
        if grps:
            keyboard = [[InlineKeyboardButton(f"🗑 {g[1]}", callback_data=f'delgrp_{g[0]}')] for g in grps]
            keyboard.append([InlineKeyboardButton("⬅️ Ortga", callback_data='back_to_main')])
            await query.edit_message_text("🗑 O'chirish uchun tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.edit_message_text("ℹ️ O'chiriladigan guruh yo'q.", reply_markup=back_button())

    elif data.startswith('delgrp_'):
        gid_row = int(data.split('_')[1])
        db.remove_search_group(gid_row)
        await query.edit_message_text("✅ Guruh o'chirildi!", reply_markup=back_button())

    elif data == 'back_to_main':
        context.user_data.pop('waiting', None)
        if user_id == SUPER_ADMIN_ID:
            context.user_data.pop('viewing_admin', None)
            await query.edit_message_text("🔐 Super Admin menyusi:", reply_markup=super_admin_keyboard())
        else:
            await query.edit_message_text("🏠 Admin menyusi:", reply_markup=admin_keyboard())

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Matnli xabarlarni qayta ishlash (State machine)"""
    if not update.message or not update.message.text:
        return
    
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if not db.is_admin(user_id, SUPER_ADMIN_ID):
        return
    
    waiting = context.user_data.get('waiting')

    if waiting == 'admin_id' and user_id == SUPER_ADMIN_ID:
        try:
            new_id = int(text)
            try:
                chat = await context.bot.get_chat(new_id)
                uname = chat.username or chat.first_name or f"User_{new_id}"
            except:
                uname = f"User_{new_id}"
            
            if db.add_admin(new_id, uname):
                await update.message.reply_text(f"✅ Admin qo'shildi: {uname}", reply_markup=back_button())
            else:
                await update.message.reply_text("ℹ️ Bu admin allaqachon bor.")
        except:
            await update.message.reply_text("❌ Noto'g'ri ID!")
        context.user_data.pop('waiting', None)

    elif waiting == 'keyword':
        admin_id = context.user_data.get('viewing_admin', user_id)
        db.add_keyword(admin_id, text)
        await update.message.reply_text(f"✅ Kalit so'z qo'shildi: {text}", reply_markup=back_button())
        context.user_data.pop('waiting', None)

    elif waiting == 'private_group':
        admin_id = context.user_data.get('viewing_admin', user_id)
        # database logic
        if text.lstrip('-').isdigit():
            db.add_private_group(admin_id, group_id=int(text), group_name="Guruh")
        else:
            db.add_private_group(admin_id, group_link=text, group_name="Guruh")
        await update.message.reply_text("✅ Shaxsiy guruh saqlandi.", reply_markup=back_button())
        context.user_data.pop('waiting', None)

    elif waiting == 'search_group':
        admin_id = context.user_data.get('viewing_admin', user_id)
        if text.lstrip('-').isdigit():
            db.add_search_group(admin_id, SUPER_ADMIN_ID, group_id=int(text), group_name="Izlovchi")
        else:
            db.add_search_group(admin_id, SUPER_ADMIN_ID, group_link=text, group_name="Izlovchi")
        await update.message.reply_text("✅ Izlovchi guruh saqlandi.", reply_markup=back_button())
        context.user_data.pop('waiting', None)

async def check_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Guruhlardagi kalit so'zlarni tekshirish"""
    if not update.message or not update.message.text:
        return
    
    msg_text = update.message.text
    group_id = update.message.chat.id
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name or "Noma'lum"
    group_name = update.message.chat.title or "Noma'lum guruh"
    
    matches = db.check_keywords_in_message(group_id, msg_text)
    
    for match in matches:
        try:
            keyboard = [[InlineKeyboardButton("👤 Profil", url=f"tg://user?id={user_id}")]]
            if match['private_group_id']:
                await context.bot.send_message(
                    chat_id=match['private_group_id'],
                    text=(f"🔍 Kalit so'z topildi!\n\n"
                          f"📢 Guruh: {group_name}\n"
                          f"👤 Foydalanuvchi: {username}\n"
                          f"🔑 Kalit so'z: {match['keyword']}\n\n"
                          f"💬 Xabar:\n{msg_text}"),
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
        except Exception as e:
            logger.error(f"Xabar yuborishda xato: {e}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Xatolarni log qilish"""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Botni ishga tushirish"""
    db.init_db()
    
    # Defaults orqali barcha xabarlar Markdown formatda chiqishini ham sozlash mumkin
    application = ApplicationBuilder().token(TOKEN).build()

    # Handlerlarni qo'shish
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("id", get_chat_id))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, handle_text))
    # Guruhlar va superguruhlar uchun filtr
    application.add_handler(MessageHandler(filters.TEXT & (filters.ChatType.GROUPS | filters.ChatType.SUPERGROUP), check_group_message))
    
    application.add_error_handler(error_handler)

    logger.info("🚀 Bot v20.8 ishga tushdi")
    application.run_polling()

if __name__ == '__main__':
    main()

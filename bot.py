import logging
import os
from datetime import datetime
from dotenv import load_dotenv

# python-telegram-bot v20+ modullari
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
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
SUPER_ADMIN_ID = int(os.getenv('SUPER_ADMIN_ID'))

if not TOKEN or not SUPER_ADMIN_ID:
    raise ValueError("❌ .env faylida BOT_TOKEN yoki SUPER_ADMIN_ID topilmadi!")

# ==================== KEYBOARD ====================

def super_admin_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Yangi admin qo'shish", callback_data='add_admin')],
        [InlineKeyboardButton("📋 Adminlar ro'yxati", callback_data='list_admins')],
        [InlineKeyboardButton("🗑 Admin o'chirish", callback_data='remove_admin')],
        [InlineKeyboardButton("🚪 Admin xonasiga o'tish", callback_data='enter_admin_room')],
        [InlineKeyboardButton("🔧 Userbot sozlamalari", callback_data='userbot_settings')],
        [InlineKeyboardButton("🤖 Userbotni tekshirish", callback_data='check_userbot')]
    ])

def admin_keyboard():
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
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ortga", callback_data='back_to_main')]])

# ==================== HANDLERS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
    if user_id == SUPER_ADMIN_ID:
        await update.message.reply_text(
            "🔐 Assalomu alaykum, Super Admin!\n\n"
            "Menyudan kerakli bo'limni tanlang:",
            reply_markup=super_admin_keyboard()
        )
    elif db.is_admin(user_id, SUPER_ADMIN_ID):
        await update.message.reply_text(
            f"👋 Assalomu alaykum, {username}!\n\n"
            f"🏠 Shaxsiy xonangizga xush kelibsiz.",
            reply_markup=admin_keyboard()
        )
    else:
        keyboard = [[InlineKeyboardButton("👤 Adminga bog'lanish", url=f"tg://user?id={SUPER_ADMIN_ID}")]]
        await update.message.reply_text(
            f"👋 Assalomu alaykum, {username}!\n\n⚠️ Botdan faqat adminlar foydalana oladi!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    chat_title = update.effective_chat.title if update.effective_chat.title else "Shaxsiy chat"
    
    await update.message.reply_text(
        f"📊 Chat ma'lumotlari:\n\n📝 Nomi: {chat_title}\n🆔 ID: `{chat_id}`\n📁 Turi: {chat_type}",
        parse_mode='Markdown'
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    # ========== SUPER ADMIN FUNKSIYALARI ==========
    
    if data == 'add_admin' and user_id == SUPER_ADMIN_ID:
        context.user_data['waiting'] = 'admin_id'
        await query.edit_message_text("📝 Yangi admin ID raqamini yuboring:", reply_markup=back_button())

    elif data == 'list_admins' and user_id == SUPER_ADMIN_ID:
        admins = db.get_all_admins()
        if admins:
            keyboard = [[InlineKeyboardButton(f"👤 {u} (ID: {i})", url=f"tg://user?id={i}")] for i, u in admins]
            keyboard.append([InlineKeyboardButton("⬅️ Ortga", callback_data='back_to_main')])
            await query.edit_message_text(f"📋 Adminlar ro'yxati ({len(admins)} ta):", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.edit_message_text("ℹ️ Hozircha adminlar yo'q.", reply_markup=back_button())

    elif data == 'remove_admin' and user_id == SUPER_ADMIN_ID:
        admins = db.get_all_admins()
        if admins:
            keyboard = [[InlineKeyboardButton(f"🗑 {u}", callback_data=f'rmadm_{i}')] for i, u in admins]
            keyboard.append([InlineKeyboardButton("⬅️ Ortga", callback_data='back_to_main')])
            await query.edit_message_text("🗑 O'chirish uchun adminni tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.edit_message_text("ℹ️ O'chiriladigan adminlar yo'q.", reply_markup=back_button())

    elif data.startswith('rmadm_') and user_id == SUPER_ADMIN_ID:
        admin_id = int(data.split('_')[1])
        db.remove_admin(admin_id)
        await query.edit_message_text("✅ Admin o'chirildi!", reply_markup=back_button())

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
        await query.edit_message_text(f"🏠 Admin xonasi (ID: {admin_id}):", reply_markup=admin_keyboard())

    elif data == 'userbot_settings' and user_id == SUPER_ADMIN_ID:
        stop_time = db.get_setting('userbot_stop_time', '00:00')
        start_time = db.get_setting('userbot_start_time', '02:00')
        schedule_enabled = db.get_setting('userbot_schedule_enabled', 'true')
        status = "✅ Yoqilgan" if schedule_enabled == 'true' else "❌ O'chirilgan"
        text = f"⚙️ Userbot sozlamalari:\n\n⏰ Kundalik to'xtatish: {status}\n🌙 To'xtatish: {stop_time}\n🌅 Tiklash: {start_time}"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("❌ O'chirish", callback_data='userbot_disable_schedule')], [InlineKeyboardButton("⬅️ Ortga", callback_data='back_to_main')]])
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='HTML')
        context.user_data['waiting'] = 'userbot_time'

    elif data == 'check_userbot' and user_id == SUPER_ADMIN_ID:
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
            await query.edit_message_text("ℹ️ Kalit so'zlar yo'q.", reply_markup=back_button())

    elif data.startswith('delkw_'):
        kid = int(data.split('_')[1])
        db.remove_keyword(kid)
        await query.edit_message_text("✅ O'chirildi!", reply_markup=back_button())

    elif data == 'add_private_group':
        context.user_data['waiting'] = 'private_group'
        await query.edit_message_text("📝 Shaxsiy guruh ID yoki link yuboring:", reply_markup=back_button())

    elif data == 'view_private_group':
        admin_id = context.user_data.get('viewing_admin', user_id)
        gname = db.get_private_group_name(admin_id)
        await query.edit_message_text(f"📢 Shaxsiy guruh: {gname if gname else 'Yoq'}", reply_markup=back_button())

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
            await query.edit_message_text("ℹ️ Guruhlar yo'q.", reply_markup=back_button())

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
    if not update.message or not update.message.text: return
    user_id = update.effective_user.id
    text = update.message.text.strip()
    if not db.is_admin(user_id, SUPER_ADMIN_ID): return
    waiting = context.user_data.get('waiting')

    if waiting == 'admin_id' and user_id == SUPER_ADMIN_ID:
        try:
            new_id = int(text)
            try:
                chat = await context.bot.get_chat(new_id)
                uname = chat.username or chat.first_name or f"User_{new_id}"
            except: uname = f"User_{new_id}"
            if db.add_admin(new_id, uname):
                await update.message.reply_text(f"✅ Admin qo'shildi: {uname}", reply_markup=back_button())
            else: await update.message.reply_text("ℹ️ Allaqachon mavjud.")
        except: await update.message.reply_text("❌ Xato ID.")
        context.user_data.pop('waiting', None)

    elif waiting == 'keyword':
        admin_id = context.user_data.get('viewing_admin', user_id)
        db.add_keyword(admin_id, text)
        await update.message.reply_text(f"✅ Qo'shildi: {text}", reply_markup=back_button())
        context.user_data.pop('waiting', None)

    elif waiting == 'private_group':
        admin_id = context.user_data.get('viewing_admin', user_id)
        db.add_private_group(admin_id, group_id=int(text) if text.lstrip('-').isdigit() else None, group_link=text if not text.lstrip('-').isdigit() else None, group_name="Guruh")
        await update.message.reply_text("✅ Shaxsiy guruh saqlandi.", reply_markup=back_button())
        context.user_data.pop('waiting', None)

    elif waiting == 'search_group':
        admin_id = context.user_data.get('viewing_admin', user_id)
        db.add_search_group(admin_id, SUPER_ADMIN_ID, group_id=int(text) if text.lstrip('-').isdigit() else None, group_link=text if not text.lstrip('-').isdigit() else None, group_name="Izlovchi guruh")
        await update.message.reply_text("✅ Izlovchi guruh saqlandi.", reply_markup=back_button())
        context.user_data.pop('waiting', None)

async def check_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    msg_text = update.message.text
    group_id = update.message.chat.id
    matches = db.check_keywords_in_message(group_id, msg_text)
    
    for match in matches:
        try:
            if match['private_group_id']:
                await context.bot.send_message(
                    chat_id=match['private_group_id'],
                    text=f"🔍 Topildi!\n🔑 Kalit: {match['keyword']}\n💬 Xabar: {msg_text}"
                )
        except Exception as e: logger.error(f"Xato: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")

def main():
    db.init_db()
    # v20+ uslubida ApplicationBuilder
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("id", get_chat_id))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, handle_text))
    app.add_handler(MessageHandler(filters.TEXT & (filters.ChatType.GROUPS | filters.ChatType.SUPERGROUP), check_group_message))
    app.add_error_handler(error_handler)

    logger.info("🚀 Bot v20.8 ishga tushdi")
    app.run_polling()

if __name__ == '__main__':
    main()

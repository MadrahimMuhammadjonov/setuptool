# ============================================
# bot.py - Telegram Bot (v21.10)
# ============================================

import logging
import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import database as db

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
        [InlineKeyboardButton("➕ Admin qo'shish", callback_data='add_admin')],
        [InlineKeyboardButton("📋 Adminlar", callback_data='list_admins')],
        [InlineKeyboardButton("🗑 Admin o'chirish", callback_data='remove_admin')],
        [InlineKeyboardButton("🚪 Admin xonasi", callback_data='enter_admin_room')],
        [InlineKeyboardButton("⚙️ Sozlamalar", callback_data='userbot_settings')]
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
            "Menyudan kerakli bo'limni tanlang:",
            reply_markup=super_admin_keyboard()
        )
    elif db.is_admin(user_id, SUPER_ADMIN_ID):
        await update.message.reply_text(
            f"👋 Assalomu alaykum, {username}!\n\n"
            f"🏠 Admin panelingiz:",
            reply_markup=admin_keyboard()
        )
    else:
        keyboard = [[InlineKeyboardButton("👤 Adminga bog'lanish", url=f"tg://user?id={SUPER_ADMIN_ID}")]]
        await update.message.reply_text(
            f"👋 Assalomu alaykum, {username}!\n\n"
            f"⚠️ Botdan faqat adminlar foydalana oladi!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Guruh ID olish"""
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    chat_title = getattr(update.effective_chat, 'title', "Shaxsiy chat")
    
    await update.message.reply_text(
        f"📊 Chat ma'lumotlari:\n\n"
        f"📝 Nomi: {chat_title}\n"
        f"🆔 ID: `{chat_id}`\n"
        f"📁 Turi: {chat_type}",
        parse_mode='Markdown'
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inline button callback"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    # ========== SUPER ADMIN ==========
    
    if data == 'add_admin' and user_id == SUPER_ADMIN_ID:
        context.user_data['waiting'] = 'admin_id'
        await query.edit_message_text(
            "📝 Yangi admin ID raqamini yuboring:",
            reply_markup=back_button()
        )

    elif data == 'list_admins' and user_id == SUPER_ADMIN_ID:
        admins = db.get_all_admins()
        if admins:
            text = f"📋 Adminlar ro'yxati ({len(admins)} ta):\n\n"
            for i, (aid, aname) in enumerate(admins, 1):
                text += f"{i}. {aname} (ID: {aid})\n"
            await query.edit_message_text(text, reply_markup=back_button())
        else:
            await query.edit_message_text("ℹ️ Adminlar yo'q.", reply_markup=back_button())

    elif data == 'remove_admin' and user_id == SUPER_ADMIN_ID:
        admins = db.get_all_admins()
        if admins:
            keyboard = [[InlineKeyboardButton(f"🗑 {u}", callback_data=f'rmadm_{i}')] for i, u in admins]
            keyboard.append([InlineKeyboardButton("⬅️ Ortga", callback_data='back_to_main')])
            await query.edit_message_text(
                "🗑 O'chirish uchun adminni tanlang:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
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
            f"🏠 Admin xonasi (ID: {admin_id}):",
            reply_markup=admin_keyboard()
        )

    elif data == 'userbot_settings' and user_id == SUPER_ADMIN_ID:
        stop_time = db.get_setting('userbot_stop_time', '00:00')
        start_time = db.get_setting('userbot_start_time', '02:00')
        enabled = db.get_setting('userbot_schedule_enabled', 'true')
        
        status = "✅ Yoqilgan" if enabled == 'true' else "❌ O'chirilgan"
        text = f"⚙️ Sozlamalar:\n\n⏰ Status: {status}\n"
        
        if enabled == 'true':
            text += f"🌙 To'xtash: {stop_time}\n🌅 Ishga tushish: {start_time}"
        
        await query.edit_message_text(text, reply_markup=back_button())

    # ========== ADMIN ==========
    
    elif data == 'back_to_main':
        context.user_data.clear()
        if user_id == SUPER_ADMIN_ID:
            await query.edit_message_text("🔐 Super Admin menyusi:", reply_markup=super_admin_keyboard())
        else:
            await query.edit_message_text("🏠 Admin menyusi:", reply_markup=admin_keyboard())

    elif data == 'add_keyword':
        context.user_data['waiting'] = 'keyword'
        await query.edit_message_text(
            "📝 Kalit so'zni yuboring:\n\n"
            "💡 Vergul bilan ajratib bir nechta yuboring.",
            reply_markup=back_button()
        )

    elif data == 'view_keywords':
        admin_id = context.user_data.get('viewing_admin', user_id)
        keywords = db.get_admin_keywords(admin_id)
        if keywords:
            text = "📋 Kalit so'zlar:\n\n"
            for i, k in enumerate(keywords, 1):
                text += f"{i}. {k}\n"
            await query.edit_message_text(text, reply_markup=back_button())
        else:
            await query.edit_message_text("ℹ️ Kalit so'zlar yo'q.", reply_markup=back_button())

    elif data == 'delete_keyword':
        admin_id = context.user_data.get('viewing_admin', user_id)
        keywords = db.get_admin_keywords(admin_id)
        if keywords:
            keyboard = [[InlineKeyboardButton(f"🗑 {k}", callback_data=f'delkey_{k}')] for k in keywords]
            keyboard.append([InlineKeyboardButton("⬅️ Ortga", callback_data='back_to_main')])
            await query.edit_message_text(
                "🗑 O'chirish uchun tanlang:",
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
            "📝 Shaxsiy guruh ID raqamini yuboring:\n\n"
            "💡 Guruhda /id buyrug'ini bering.",
            reply_markup=back_button()
        )

    elif data == 'view_private_group':
        admin_id = context.user_data.get('viewing_admin', user_id)
        groups = db.get_admin_private_groups(admin_id)
        if groups:
            text = "👁 Shaxsiy guruhlar:\n\n"
            for i, (gid, gname, glink) in enumerate(groups, 1):
                text += f"{i}. {gname or 'Guruh'} (ID: {gid})\n"
            await query.edit_message_text(text, reply_markup=back_button())
        else:
            await query.edit_message_text("ℹ️ Shaxsiy guruhlar yo'q.", reply_markup=back_button())

    elif data == 'delete_private_group':
        admin_id = context.user_data.get('viewing_admin', user_id)
        groups = db.get_admin_private_groups(admin_id)
        if groups:
            keyboard = [[InlineKeyboardButton(f"🗑 {name or 'Guruh'}", callback_data=f'delpriv_{gid}')] 
                       for gid, name, link in groups]
            keyboard.append([InlineKeyboardButton("⬅️ Ortga", callback_data='back_to_main')])
            await query.edit_message_text("🗑 O'chirish uchun tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.edit_message_text("ℹ️ O'chiriladigan guruhlar yo'q.", reply_markup=back_button())

    elif data.startswith('delpriv_'):
        admin_id = context.user_data.get('viewing_admin', user_id)
        group_id = int(data.split('_')[1])
        db.remove_private_group(admin_id, group_id)
        await query.edit_message_text("✅ Guruh o'chirildi!", reply_markup=back_button())

    elif data == 'add_search_group':
        context.user_data['waiting'] = 'search_group'
        await query.edit_message_text(
            "📝 Izlovchi guruh ID raqamini yuboring:",
            reply_markup=back_button()
        )

    elif data == 'view_search_groups':
        admin_id = context.user_data.get('viewing_admin', user_id)
        groups = db.get_admin_search_groups(admin_id)
        if groups:
            text = "📋 Izlovchi guruhlar:\n\n"
            for i, (gid, gname, glink) in enumerate(groups, 1):
                text += f"{i}. {gname or 'Guruh'} (ID: {gid})\n"
            await query.edit_message_text(text, reply_markup=back_button())
        else:
            await query.edit_message_text("ℹ️ Izlovchi guruhlar yo'q.", reply_markup=back_button())

    elif data == 'delete_search_group':
        admin_id = context.user_data.get('viewing_admin', user_id)
        groups = db.get_admin_search_groups(admin_id)
        if groups:
            keyboard = [[InlineKeyboardButton(f"🗑 {name or 'Guruh'}", callback_data=f'delsrch_{gid}')] 
                       for gid, name, link in groups]
            keyboard.append([InlineKeyboardButton("⬅️ Ortga", callback_data='back_to_main')])
            await query.edit_message_text("🗑 O'chirish uchun tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.edit_message_text("ℹ️ O'chiriladigan guruhlar yo'q.", reply_markup=back_button())

    elif data.startswith('delsrch_'):
        admin_id = context.user_data.get('viewing_admin', user_id)
        group_id = int(data.split('_')[1])
        db.remove_search_group(admin_id, group_id)
        await query.edit_message_text("✅ Guruh o'chirildi!", reply_markup=back_button())

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Matnli xabarlar"""
    user_id = update.effective_user.id
    text = update.message.text
    waiting = context.user_data.get('waiting')

    if not waiting:
        return

    if waiting == 'admin_id' and user_id == SUPER_ADMIN_ID:
        try:
            new_admin_id = int(text)
            if db.add_admin(new_admin_id, f"Admin_{new_admin_id}"):
                await update.message.reply_text(f"✅ Admin qo'shildi! (ID: {new_admin_id})", 
                                              reply_markup=back_button())
            else:
                await update.message.reply_text("⚠️ Bu admin allaqachon mavjud!", reply_markup=back_button())
        except ValueError:
            await update.message.reply_text("❌ Faqat raqam yuboring!")
        context.user_data.pop('waiting', None)

    elif waiting == 'keyword':
        admin_id = context.user_data.get('viewing_admin', user_id)
        keywords = [k.strip() for k in text.split(',') if k.strip()]
        for k in keywords:
            db.add_keyword(admin_id, k)
        await update.message.reply_text(f"✅ {len(keywords)} ta kalit so'z qo'shildi!", 
                                       reply_markup=back_button())
        context.user_data.pop('waiting', None)

    elif waiting == 'private_group':
        admin_id = context.user_data.get('viewing_admin', user_id)
        try:
            gid = int(text)
            try:
                chat = await context.bot.get_chat(gid)
                gname = chat.title or f"Guruh {gid}"
            except:
                gname = f"Guruh {gid}"
            db.add_private_group(admin_id, group_id=gid, group_name=gname)
            await update.message.reply_text(f"✅ Shaxsiy guruh qo'shildi: {gname}", 
                                          reply_markup=back_button())
        except:
            await update.message.reply_text("❌ Noto'g'ri ID!", reply_markup=back_button())
        context.user_data.pop('waiting', None)

    elif waiting == 'search_group':
        admin_id = context.user_data.get('viewing_admin', user_id)
        try:
            gid = int(text)
            try:
                chat = await context.bot.get_chat(gid)
                gname = chat.title or f"Guruh {gid}"
            except:
                gname = f"Guruh {gid}"
            
            success, message = db.add_search_group(admin_id, SUPER_ADMIN_ID, group_id=gid, group_name=gname)
            await update.message.reply_text(f"{message}: {gname}", reply_markup=back_button())
        except:
            await update.message.reply_text("❌ Noto'g'ri ID!", reply_markup=back_button())
        context.user_data.pop('waiting', None)

async def check_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Guruh xabarlarini tekshirish"""
    if not update.message or not update.message.text:
        return
    
    chat_type = update.message.chat.type
    if chat_type not in ['group', 'supergroup']:
        return
    
    msg_text = update.message.text
    group_id = update.message.chat.id
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name or "Unknown"
    group_name = update.message.chat.title or "Unknown"
    
    matches = db.check_keywords_in_message(group_id, msg_text)
    
    for match in matches:
        try:
            if match['private_group_id']:
                keyboard = [[InlineKeyboardButton("👤 Profil", url=f"tg://user?id={user_id}")]]
                await context.bot.send_message(
                    chat_id=match['private_group_id'],
                    text=(f"🔍 Kalit so'z topildi!\n\n"
                          f"📢 Guruh: {group_name}\n"
                          f"👤 User: {username}\n"
                          f"🔑 Kalit: {match['keyword']}\n\n"
                          f"💬 Xabar:\n{msg_text}"),
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
        except Exception as e:
            logger.error(f"Xabar yuborishda xato: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xatolarni log qilish"""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Bot ishga tushirish"""
    logger.info("🤖 BOT ISHGA TUSHMOQDA")
    
    db.init_db()
    
    if not db.get_setting('userbot_stop_time'):
        db.set_setting('userbot_stop_time', '00:00')
        db.set_setting('userbot_start_time', '02:00')
        db.set_setting('userbot_schedule_enabled', 'true')
    
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("id", get_chat_id))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, handle_text))
    application.add_handler(MessageHandler(filters.TEXT & (filters.ChatType.GROUPS | filters.ChatType.SUPERGROUP), 
                                         check_group_message))
    application.add_error_handler(error_handler)

    logger.info("🚀 Bot ishga tushdi!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

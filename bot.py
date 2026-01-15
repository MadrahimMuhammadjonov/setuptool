# ============================================
# bot.py - Telegram Bot with Webhook (Railway optimized)
# ============================================

import logging
import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import database as db

load_dotenv()

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Settings
TOKEN = os.getenv('BOT_TOKEN')
SUPER_ADMIN_ID = int(os.getenv('SUPER_ADMIN_ID'))
WEBHOOK_URL = os.getenv('RAILWAY_PUBLIC_DOMAIN', '')  # Railway avtomatik beradi
PORT = int(os.getenv('PORT', 8080))

if not TOKEN or not SUPER_ADMIN_ID:
    raise ValueError("❌ BOT_TOKEN yoki SUPER_ADMIN_ID topilmadi!")

# ==================== KEYBOARDS ====================

def super_admin_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Admin qo'shish", callback_data='add_admin')],
        [InlineKeyboardButton("📋 Adminlar", callback_data='list_admins')],
        [InlineKeyboardButton("🗑 Admin o'chirish", callback_data='remove_admin')],
        [InlineKeyboardButton("🚪 Admin xonasi", callback_data='enter_admin_room')]
    ])

def admin_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Kalit so'z", callback_data='add_keyword'), 
         InlineKeyboardButton("📋 Ko'rish", callback_data='view_keywords')],
        [InlineKeyboardButton("🗑 O'chirish", callback_data='delete_keyword')],
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
            "🔐 Assalomu alaykum, Super Admin!",
            reply_markup=super_admin_keyboard()
        )
    elif db.is_admin(user_id, SUPER_ADMIN_ID):
        await update.message.reply_text(
            f"👋 Assalomu alaykum, {username}!",
            reply_markup=admin_keyboard()
        )
    else:
        keyboard = [[InlineKeyboardButton("👤 Admin", url=f"tg://user?id={SUPER_ADMIN_ID}")]]
        await update.message.reply_text(
            "⚠️ Botdan faqat adminlar foydalana oladi!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    chat_title = getattr(update.effective_chat, 'title', "Shaxsiy chat")
    
    await update.message.reply_text(
        f"📊 Chat:\n📝 {chat_title}\n🆔 `{chat_id}`\n📁 {chat_type}",
        parse_mode='Markdown'
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    # SUPER ADMIN
    if data == 'add_admin' and user_id == SUPER_ADMIN_ID:
        context.user_data['waiting'] = 'admin_id'
        await query.edit_message_text("📝 Admin ID raqamini yuboring:", reply_markup=back_button())

    elif data == 'list_admins' and user_id == SUPER_ADMIN_ID:
        admins = db.get_all_admins()
        if admins:
            text = f"📋 Adminlar ({len(admins)} ta):\n\n"
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
            await query.edit_message_text("🗑 O'chirish:", reply_markup=InlineKeyboardMarkup(keyboard))
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
            await query.edit_message_text("🚪 Admin xonasi:", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.edit_message_text("ℹ️ Adminlar yo'q.", reply_markup=back_button())

    elif data.startswith('enter_') and user_id == SUPER_ADMIN_ID:
        admin_id = int(data.split('_')[1])
        context.user_data['viewing_admin'] = admin_id
        await query.edit_message_text(f"🏠 Admin xonasi (ID: {admin_id}):", reply_markup=admin_keyboard())

    # ADMIN FUNCTIONS
    elif data == 'back_to_main':
        context.user_data.clear()
        if user_id == SUPER_ADMIN_ID:
            await query.edit_message_text("🔐 Super Admin:", reply_markup=super_admin_keyboard())
        else:
            await query.edit_message_text("🏠 Admin panel:", reply_markup=admin_keyboard())

    elif data == 'add_keyword':
        context.user_data['waiting'] = 'keyword'
        await query.edit_message_text("📝 Kalit so'z yuboring:", reply_markup=back_button())

    elif data == 'view_keywords':
        admin_id = context.user_data.get('viewing_admin', user_id)
        keywords = db.get_admin_keywords(admin_id)
        if keywords:
            text = "📋 Kalit so'zlar:\n\n" + "\n".join([f"{i}. {k}" for i, k in enumerate(keywords, 1)])
            await query.edit_message_text(text, reply_markup=back_button())
        else:
            await query.edit_message_text("ℹ️ Kalit so'zlar yo'q.", reply_markup=back_button())

    elif data == 'delete_keyword':
        admin_id = context.user_data.get('viewing_admin', user_id)
        keywords = db.get_admin_keywords(admin_id)
        if keywords:
            keyboard = [[InlineKeyboardButton(f"🗑 {k}", callback_data=f'delkey_{k}')] for k in keywords]
            keyboard.append([InlineKeyboardButton("⬅️ Ortga", callback_data='back_to_main')])
            await query.edit_message_text("🗑 O'chirish:", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.edit_message_text("ℹ️ Kalit so'zlar yo'q.", reply_markup=back_button())

    elif data.startswith('delkey_'):
        admin_id = context.user_data.get('viewing_admin', user_id)
        keyword = data.replace('delkey_', '')
        db.remove_keyword(admin_id, keyword)
        await query.edit_message_text(f"✅ '{keyword}' o'chirildi!", reply_markup=back_button())

    elif data == 'add_private_group':
        context.user_data['waiting'] = 'private_group'
        await query.edit_message_text("📝 Shaxsiy guruh ID:", reply_markup=back_button())

    elif data == 'view_private_group':
        admin_id = context.user_data.get('viewing_admin', user_id)
        groups = db.get_admin_private_groups(admin_id)
        if groups:
            text = "👁 Shaxsiy guruhlar:\n\n"
            for i, (gid, gname, _) in enumerate(groups, 1):
                text += f"{i}. {gname or 'Guruh'} (ID: {gid})\n"
            await query.edit_message_text(text, reply_markup=back_button())
        else:
            await query.edit_message_text("ℹ️ Guruhlar yo'q.", reply_markup=back_button())

    elif data == 'delete_private_group':
        admin_id = context.user_data.get('viewing_admin', user_id)
        groups = db.get_admin_private_groups(admin_id)
        if groups:
            keyboard = [[InlineKeyboardButton(f"🗑 {n or 'Guruh'}", callback_data=f'delpriv_{g}')] 
                       for g, n, _ in groups]
            keyboard.append([InlineKeyboardButton("⬅️ Ortga", callback_data='back_to_main')])
            await query.edit_message_text("🗑 O'chirish:", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.edit_message_text("ℹ️ Guruhlar yo'q.", reply_markup=back_button())

    elif data.startswith('delpriv_'):
        admin_id = context.user_data.get('viewing_admin', user_id)
        group_id = int(data.split('_')[1])
        db.remove_private_group(admin_id, group_id)
        await query.edit_message_text("✅ Guruh o'chirildi!", reply_markup=back_button())

    elif data == 'add_search_group':
        context.user_data['waiting'] = 'search_group'
        await query.edit_message_text("📝 Izlovchi guruh ID:", reply_markup=back_button())

    elif data == 'view_search_groups':
        admin_id = context.user_data.get('viewing_admin', user_id)
        groups = db.get_admin_search_groups(admin_id)
        if groups:
            text = "📋 Izlovchi guruhlar:\n\n"
            for i, (gid, gname, _) in enumerate(groups, 1):
                text += f"{i}. {gname or 'Guruh'} (ID: {gid})\n"
            await query.edit_message_text(text, reply_markup=back_button())
        else:
            await query.edit_message_text("ℹ️ Guruhlar yo'q.", reply_markup=back_button())

    elif data == 'delete_search_group':
        admin_id = context.user_data.get('viewing_admin', user_id)
        groups = db.get_admin_search_groups(admin_id)
        if groups:
            keyboard = [[InlineKeyboardButton(f"🗑 {n or 'Guruh'}", callback_data=f'delsrch_{g}')] 
                       for g, n, _ in groups]
            keyboard.append([InlineKeyboardButton("⬅️ Ortga", callback_data='back_to_main')])
            await query.edit_message_text("🗑 O'chirish:", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.edit_message_text("ℹ️ Guruhlar yo'q.", reply_markup=back_button())

    elif data.startswith('delsrch_'):
        admin_id = context.user_data.get('viewing_admin', user_id)
        group_id = int(data.split('_')[1])
        db.remove_search_group(admin_id, group_id)
        await query.edit_message_text("✅ Guruh o'chirildi!", reply_markup=back_button())

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
                await update.message.reply_text("⚠️ Allaqachon mavjud!", reply_markup=back_button())
        except ValueError:
            await update.message.reply_text("❌ Faqat raqam!")
        context.user_data.pop('waiting', None)

    elif waiting == 'keyword':
        admin_id = context.user_data.get('viewing_admin', user_id)
        keywords = [k.strip() for k in text.split(',') if k.strip()]
        for k in keywords:
            db.add_keyword(admin_id, k)
        await update.message.reply_text(f"✅ {len(keywords)} ta qo'shildi!", reply_markup=back_button())
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
            await update.message.reply_text(f"✅ Qo'shildi: {gname}", reply_markup=back_button())
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
            
            success, msg = db.add_search_group(admin_id, SUPER_ADMIN_ID, group_id=gid, group_name=gname)
            await update.message.reply_text(f"{msg}: {gname}", reply_markup=back_button())
        except:
            await update.message.reply_text("❌ Noto'g'ri ID!", reply_markup=back_button())
        context.user_data.pop('waiting', None)

async def check_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    
    if update.message.chat.type not in ['group', 'supergroup']:
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
                    text=(f"🔍 Topildi!\n\n📢 {group_name}\n👤 {username}\n🔑 {match['keyword']}\n\n💬 {msg_text}"),
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
        except Exception as e:
            logger.error(f"Xato: {e}")

async def error_handler(update, context):
    logger.error(f"Error: {context.error}")

def main():
    logger.info("🤖 BOT ISHGA TUSHMOQDA")
    
    db.init_db()
    
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("id", get_chat_id))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, handle_text))
    application.add_handler(MessageHandler(filters.TEXT & (filters.ChatType.GROUPS | filters.ChatType.SUPERGROUP), 
                                         check_group_message))
    application.add_error_handler(error_handler)

    logger.info("🚀 Bot tayyor!")
    
    # Railway uchun webhook yoki polling
    if WEBHOOK_URL:
        logger.info(f"📡 Webhook mode: {WEBHOOK_URL}")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=f"https://{WEBHOOK_URL}/{TOKEN}"
        )
    else:
        logger.info("🔄 Polling mode")
        application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()

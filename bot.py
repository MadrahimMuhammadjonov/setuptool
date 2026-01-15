# ============================================
# bot.py - Telegram Bot (python-telegram-bot v21.10)
# ============================================

import logging
import os
from datetime import datetime
from dotenv import load_dotenv
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

load_dotenv()

# Logging sozlash
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== SOZLAMALAR ====================
TOKEN = os.getenv('BOT_TOKEN')
SUPER_ADMIN_ID = int(os.getenv('SUPER_ADMIN_ID'))

if not TOKEN or not SUPER_ADMIN_ID:
    raise ValueError("❌ .env faylida BOT_TOKEN yoki SUPER_ADMIN_ID topilmadi!")

# ==================== YORDAMCHI FUNKSIYALAR ====================

def is_super_admin(user_id):
    """Super admin ekanligini tekshirish"""
    return user_id == SUPER_ADMIN_ID

def is_admin(user_id):
    """Admin yoki super admin ekanligini tekshirish"""
    return db.is_admin(user_id, SUPER_ADMIN_ID)

# ==================== KLAVIATURALAR ====================

def super_admin_keyboard():
    """Super admin uchun asosiy menyu"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Yangi admin qo'shish", callback_data='add_admin')],
        [InlineKeyboardButton("📋 Adminlar ro'yxati", callback_data='list_admins')],
        [InlineKeyboardButton("🗑 Admin o'chirish", callback_data='remove_admin')],
        [InlineKeyboardButton("🚪 Admin xonasiga o'tish", callback_data='enter_admin_room')]
    ])

def admin_keyboard():
    """Admin uchun asosiy menyu"""
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

# ==================== COMMAND HANDLERS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start buyrug'i - Botni ishga tushirish"""
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
    if is_super_admin(user_id):
        await update.message.reply_text(
            "🔐 Assalomu alaykum, Super Admin!\n\n"
            "Bu bot izlovchi guruhlardagi kalit so'zlarni topib, "
            "shaxsiy guruhingizga yuboradi.\n\n"
            "Menyudan kerakli bo'limni tanlang:",
            reply_markup=super_admin_keyboard()
        )
    elif is_admin(user_id):
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
    chat_title = getattr(update.effective_chat, 'title', "Shaxsiy chat")
    
    await update.message.reply_text(
        f"📊 Chat ma'lumotlari:\n\n"
        f"📝 Nomi: {chat_title}\n"
        f"🆔 ID: `{chat_id}`\n"
        f"📁 Turi: {chat_type}",
        parse_mode='Markdown'
    )

# ==================== CALLBACK HANDLERS ====================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inline tugmalar bosilganda"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    # ========== SUPER ADMIN FUNKSIYALARI ==========
    
    if data == 'add_admin' and is_super_admin(user_id):
        context.user_data['waiting'] = 'admin_id'
        await query.edit_message_text(
            "📝 Yangi admin ID raqamini yuboring:\n\n"
            "💡 ID olish: @userinfobot ga /start yuboring",
            reply_markup=back_button()
        )

    elif data == 'list_admins' and is_super_admin(user_id):
        admins = db.get_all_admins()
        if admins:
            keyboard = [[InlineKeyboardButton(f"👤 {u} (ID: {i})", url=f"tg://user?id={i}")] 
                       for i, u in admins]
            keyboard.append([InlineKeyboardButton("⬅️ Ortga", callback_data='back_to_main')])
            await query.edit_message_text(
                f"📋 Adminlar ro'yxati ({len(admins)} ta):",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.edit_message_text("ℹ️ Hozircha adminlar yo'q.", reply_markup=back_button())

    elif data == 'remove_admin' and is_super_admin(user_id):
        admins = db.get_all_admins()
        if admins:
            keyboard = [[InlineKeyboardButton(f"🗑 {u}", callback_data=f'rmadm_{i}')] 
                       for i, u in admins]
            keyboard.append([InlineKeyboardButton("⬅️ Ortga", callback_data='back_to_main')])
            await query.edit_message_text(
                "🗑 O'chirish uchun adminni tanlang:\n\n"
                "⚠️ Admin o'chirilganda uning barcha ma'lumotlari "
                "(kalit so'zlar, guruhlar) ham o'chiriladi!",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.edit_message_text("ℹ️ O'chiriladigan adminlar yo'q.", reply_markup=back_button())

    elif data.startswith('rmadm_') and is_super_admin(user_id):
        admin_id = int(data.split('_')[1])
        db.remove_admin(admin_id)
        await query.edit_message_text(
            "✅ Admin va uning barcha ma'lumotlari o'chirildi!",
            reply_markup=back_button()
        )

    elif data == 'enter_admin_room' and is_super_admin(user_id):
        admins = db.get_all_admins()
        if admins:
            keyboard = [[InlineKeyboardButton(f"🚪 {u}", callback_data=f'enter_{i}')] 
                       for i, u in admins]
            keyboard.append([InlineKeyboardButton("⬅️ Ortga", callback_data='back_to_main')])
            await query.edit_message_text(
                "🚪 Qaysi admin xonasiga kirmoqchisiz?",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.edit_message_text("ℹ️ Adminlar yo'q.", reply_markup=back_button())

    elif data.startswith('enter_') and is_super_admin(user_id):
        admin_id = int(data.split('_')[1])
        context.user_data['viewing_admin'] = admin_id
        await query.edit_message_text(
            f"🏠 Admin xonasi (ID: {admin_id}):\n\n"
            f"Ushbu xonada barcha admin funksiyalaridan foydalanishingiz mumkin.",
            reply_markup=admin_keyboard()
        )

    # ========== ADMIN FUNKSIYALARI - KALIT SO'ZLAR ==========
    
    elif data == 'back_to_main':
        context.user_data.pop('waiting', None)
        context.user_data.pop('viewing_admin', None)
        if is_super_admin(user_id):
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
            "Masalan: ish, vakansiya, usta",
            reply_markup=back_button()
        )

    elif data == 'view_keywords':
        admin_id = context.user_data.get('viewing_admin', user_id)
        keywords = db.get_admin_keywords(admin_id)
        if keywords:
            text = "📋 Sizning kalit so'zlaringiz:\n\n"
            for i, k in enumerate(keywords, 1):
                text += f"{i}. {k}\n"
            text += f"\n💾 Jami: {len(keywords)} ta"
            await query.edit_message_text(text, reply_markup=back_button())
        else:
            await query.edit_message_text("ℹ️ Kalit so'zlar topilmadi.", reply_markup=back_button())

    elif data == 'delete_keyword':
        admin_id = context.user_data.get('viewing_admin', user_id)
        keywords = db.get_admin_keywords(admin_id)
        if keywords:
            keyboard = [[InlineKeyboardButton(f"🗑 {k}", callback_data=f'delkey_{k}')] 
                       for k in keywords]
            keyboard.append([InlineKeyboardButton("⬅️ Ortga", callback_data='back_to_main')])
            await query.edit_message_text(
                "🗑 O'chirish uchun kalit so'zni tanlang:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.edit_message_text(
                "ℹ️ O'chiriladigan kalit so'zlar yo'q.", 
                reply_markup=back_button()
            )

    elif data.startswith('delkey_'):
        admin_id = context.user_data.get('viewing_admin', user_id)
        keyword = data.replace('delkey_', '')
        db.remove_keyword(admin_id, keyword)
        await query.edit_message_text(
            f"✅ '{keyword}' o'chirildi!", 
            reply_markup=back_button()
        )

    # ========== ADMIN FUNKSIYALARI - SHAXSIY GURUH ==========
    
    elif data == 'add_private_group':
        context.user_data['waiting'] = 'private_group'
        await query.edit_message_text(
            "📝 Shaxsiy guruh ID raqamini yoki linkini yuboring:\n\n"
            "💡 ID olish uchun:\n"
            "1. Botni guruhga admin qiling\n"
            "2. Guruhda /id buyrug'ini bering\n"
            "3. ID yoki linkni bu yerga yuboring",
            reply_markup=back_button()
        )

    elif data == 'view_private_group':
        admin_id = context.user_data.get('viewing_admin', user_id)
        groups = db.get_admin_private_groups(admin_id)
        if groups:
            text = "👁 Shaxsiy guruhlaringiz:\n\n"
            for i, (gid, gname, glink) in enumerate(groups, 1):
                text += f"{i}. {gname or 'Guruh'} (ID: {gid})\n"
            await query.edit_message_text(text, reply_markup=back_button())
        else:
            await query.edit_message_text("ℹ️ Shaxsiy guruhlar topilmadi.", reply_markup=back_button())

    elif data == 'delete_private_group':
        admin_id = context.user_data.get('viewing_admin', user_id)
        groups = db.get_admin_private_groups(admin_id)
        if groups:
            keyboard = [[InlineKeyboardButton(f"🗑 {name or 'Guruh'}", callback_data=f'delpriv_{gid}')] 
                       for gid, name, link in groups]
            keyboard.append([InlineKeyboardButton("⬅️ Ortga", callback_data='back_to_main')])
            await query.edit_message_text(
                "🗑 O'chirish uchun guruhni tanlang:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.edit_message_text(
                "ℹ️ O'chiriladigan guruhlar yo'q.", 
                reply_markup=back_button()
            )

    elif data.startswith('delpriv_'):
        admin_id = context.user_data.get('viewing_admin', user_id)
        group_id = int(data.split('_')[1])
        db.remove_private_group(admin_id, group_id)
        await query.edit_message_text("✅ Shaxsiy guruh o'chirildi!", reply_markup=back_button())

    # ========== ADMIN FUNKSIYALARI - IZLOVCHI GURUHLAR ==========
    
    elif data == 'add_search_group':
        admin_id = context.user_data.get('viewing_admin', user_id)
        groups = db.get_admin_search_groups(admin_id)
        context.user_data['waiting'] = 'search_group'
        await query.edit_message_text(
            f"📝 Izlovchi guruh ID raqamini yoki linkini yuboring:\n\n"
            f"📊 Hozirda: {len(groups)}/100 ta\n\n"
            f"💡 ID olish uchun:\n"
            f"1. Botni guruhga admin qiling\n"
            f"2. Guruhda /id buyrug'ini bering\n"
            f"3. ID yoki linkni bu yerga yuboring",
            reply_markup=back_button()
        )

    elif data == 'view_search_groups':
        admin_id = context.user_data.get('viewing_admin', user_id)
        groups = db.get_admin_search_groups(admin_id)
        if groups:
            text = "📋 Izlovchi guruhlar:\n\n"
            for i, (gid, gname, glink) in enumerate(groups, 1):
                text += f"{i}. {gname or 'Guruh'} (ID: {gid})\n"
            text += f"\n💾 Jami: {len(groups)}/100 ta"
            await query.edit_message_text(text, reply_markup=back_button())
        else:
            await query.edit_message_text("ℹ️ Izlovchi guruhlar topilmadi.", reply_markup=back_button())

    elif data == 'delete_search_group':
        admin_id = context.user_data.get('viewing_admin', user_id)
        groups = db.get_admin_search_groups(admin_id)
        if groups:
            keyboard = [[InlineKeyboardButton(f"🗑 {name or 'Guruh'}", callback_data=f'delsrch_{gid}')] 
                       for gid, name, link in groups]
            keyboard.append([InlineKeyboardButton("⬅️ Ortga", callback_data='back_to_main')])
            await query.edit_message_text(
                "🗑 O'chirish uchun guruhni tanlang:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.edit_message_text(
                "ℹ️ O'chiriladigan guruhlar yo'q.", 
                reply_markup=back_button()
            )

    elif data.startswith('delsrch_'):
        admin_id = context.user_data.get('viewing_admin', user_id)
        group_id = int(data.split('_')[1])
        db.remove_search_group(admin_id, group_id)
        await query.edit_message_text("✅ Izlovchi guruh o'chirildi!", reply_markup=back_button())

# ==================== TEXT MESSAGE HANDLERS ====================

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shaxsiy chatda matnli xabarlarni qayta ishlash"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    waiting = context.user_data.get('waiting')

    if not waiting:
        return

    # Admin ID qo'shish
    if waiting == 'admin_id' and is_super_admin(user_id):
        try:
            new_admin_id = int(text)
            # Admin ma'lumotlarini olishga harakat
            try:
                chat = await context.bot.get_chat(new_admin_id)
                username = chat.username or chat.first_name or f"Admin_{new_admin_id}"
            except:
                username = f"Admin_{new_admin_id}"
            
            if db.add_admin(new_admin_id, username):
                await update.message.reply_text(
                    f"✅ Yangi admin qo'shildi!\n\n"
                    f"👤 {username}\n"
                    f"🆔 {new_admin_id}",
                    reply_markup=back_button()
                )
            else:
                await update.message.reply_text(
                    "⚠️ Bu admin allaqachon mavjud!",
                    reply_markup=back_button()
                )
        except ValueError:
            await update.message.reply_text("❌ Noto'g'ri ID! Faqat raqam yuboring.")
        context.user_data.pop('waiting', None)

    # Kalit so'z qo'shish
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

    # Shaxsiy guruh qo'shish
    elif waiting == 'private_group':
        admin_id = context.user_data.get('viewing_admin', user_id)
        if text.startswith("http"):
            # Link orqali
            db.add_private_group(admin_id, group_link=text, group_name="Link orqali guruh")
            await update.message.reply_text(
                "✅ Shaxsiy guruh qo'shildi: Link orqali guruh",
                reply_markup=back_button()
            )
        else:
            # ID orqali
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

    # Izlovchi guruh qo'shish
    elif waiting == 'search_group':
        admin_id = context.user_data.get('viewing_admin', user_id)
        if text.startswith("http"):
            # Link orqali
            success, message = db.add_search_group(
                admin_id, SUPER_ADMIN_ID, 
                group_link=text, 
                group_name="Link orqali guruh"
            )
            if success:
                await update.message.reply_text(
                    f"✅ {message}: Link orqali guruh",
                    reply_markup=back_button()
                )
            else:
                await update.message.reply_text(f"❌ {message}", reply_markup=back_button())
        else:
            # ID orqali
            try:
                gid = int(text)
                try:
                    chat = await context.bot.get_chat(gid)
                    gname = chat.title or f"Guruh {gid}"
                except:
                    gname = f"Guruh {gid}"
                
                success, message = db.add_search_group(
                    admin_id, SUPER_ADMIN_ID, 
                    group_id=gid, 
                    group_name=gname
                )
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

# ==================== GROUP MESSAGE HANDLER ====================

async def check_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Guruh xabarlarini tekshirish va kalit so'zlarni qidirish"""
    if not update.message or not update.message.text:
        return
    
    chat_type = update.message.chat.type
    if chat_type not in ['group', 'supergroup']:
        return
    
    msg_text = update.message.text
    group_id = update.message.chat.id
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name or "Noma'lum"
    group_name = update.message.chat.title or "Noma'lum guruh"
    
    # Kalit so'zlarni tekshirish
    matches = db.check_keywords_in_message(group_id, msg_text)
    
    # Topilgan har bir kalit so'z uchun xabar yuborish
    for match in matches:
        try:
            if match['private_group_id']:
                keyboard = [[InlineKeyboardButton("👤 Profil", url=f"tg://user?id={user_id}")]]
                await context.bot.send_message(
                    chat_id=match['private_group_id'],
                    text=(
                        f"🔍 Kalit so'z topildi!\n\n"
                        f"📢 Guruh: {group_name}\n"
                        f"👤 Foydalanuvchi: {username}\n"
                        f"🆔 User ID: {user_id}\n"
                        f"🔑 Kalit so'z: {match['keyword']}\n\n"
                        f"💬 Xabar:\n{msg_text}"
                    ),
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
        except Exception as e:
            logger.error(f"Xabar yuborishda xatolik: {e}")

# ==================== ERROR HANDLER ====================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xatolarni qayd qilish"""
    logger.error(f"Update {update} xatolikka sabab bo'ldi: {context.error}")

# ==================== MAIN ====================

def main():
    """Botni ishga tushirish"""
    logger.info("=" * 60)
    logger.info("🤖 BOT ISHGA TUSHMOQDA")
    logger.info("=" * 60)
    
    # Database yaratish
    db.init_db()
    
    # Application yaratish
    application = ApplicationBuilder().token(TOKEN).build()

    # Handlerlarni qo'shish
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("id", get_chat_id))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, handle_text))
    application.add_handler(MessageHandler(
        filters.TEXT & (filters.ChatType.GROUPS | filters.ChatType.SUPERGROUP), 
        check_group_message
    ))
    application.add_error_handler(error_handler)

    logger.info("✅ Bot tayyor!")
    logger.info("🚀 Bot ishlamoqda...")
    
    # Botni ishga tushirish
    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )

if __name__ == '__main__':
    main()

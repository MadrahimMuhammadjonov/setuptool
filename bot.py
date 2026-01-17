# ============================================
# bot.py - Telegram Bot
# ============================================

import logging
import os
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
import database as db

# .env fayldan sozlamalarni yuklash
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

def start(update: Update, context: CallbackContext):
    """Start command handler"""
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name

    if user_id == SUPER_ADMIN_ID:
        update.message.reply_text(
            "🔐 Assalomu alaykum, Super Admin!\n\nMenyudan kerakli bo'limni tanlang:",
            reply_markup=super_admin_keyboard()
        )
    elif db.is_admin(user_id, SUPER_ADMIN_ID):
        update.message.reply_text(
            f"👋 Assalomu alaykum, {username}!\n\n🏠 Shaxsiy xonangizga xush kelibsiz:",
            reply_markup=admin_keyboard()
        )
    else:
        keyboard = [[InlineKeyboardButton("👤 Adminga bog'lanish", url=f"tg://user?id={SUPER_ADMIN_ID}")]]
        update.message.reply_text(
            f"👋 Assalomu alaykum, {username}!\n\n⚠️ Botdan faqat adminlar foydalana oladi!\nBotdan foydalanish uchun adminga murojaat qiling!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

def get_chat_id(update: Update, context: CallbackContext):
    """Guruh ID olish"""
    chat_id = update.effective_chat.id
    update.message.reply_text(f"📊 Bu guruh ID: `{chat_id}`", parse_mode='Markdown')

def button_callback(update: Update, context: CallbackContext):
    """Inline button callback handler"""
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    data = query.data

    # ========== SUPER ADMIN FUNKSIYALARI ==========

    if data == 'add_admin' and user_id == SUPER_ADMIN_ID:
        context.user_data['waiting'] = 'admin_id'
        query.edit_message_text("📝 Yangi admin ID raqamini yuboring:", reply_markup=back_button())

    elif data == 'list_admins' and user_id == SUPER_ADMIN_ID:
        admins = db.get_all_admins()
        if admins:
            keyboard = [[InlineKeyboardButton(f"👤 {u} (ID: {i})", url=f"tg://user?id={i}")] for i, u in admins]
            keyboard.append([InlineKeyboardButton("⬅️ Ortga", callback_data='back_to_main')])
            query.edit_message_text(f"📋 Adminlar ro'yxati ({len(admins)} ta):", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            query.edit_message_text("ℹ️ Adminlar yo'q.", reply_markup=back_button())

    elif data == 'remove_admin' and user_id == SUPER_ADMIN_ID:
        admins = db.get_all_admins()
        if admins:
            keyboard = [[InlineKeyboardButton(f"🗑 {u}", callback_data=f'rmadm_{i}')] for i, u in admins]
            keyboard.append([InlineKeyboardButton("⬅️ Ortga", callback_data='back_to_main')])
            query.edit_message_text("🗑 O'chirish uchun adminni tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            query.edit_message_text("ℹ️ Adminlar yo'q.", reply_markup=back_button())

    elif data.startswith('rmadm_') and user_id == SUPER_ADMIN_ID:
        admin_id = int(data.split('_')[1])
        db.remove_admin(admin_id)
        query.edit_message_text("✅ Admin o'chirildi!", reply_markup=back_button())

    elif data == 'enter_admin_room' and user_id == SUPER_ADMIN_ID:
        admins = db.get_all_admins()
        if admins:
            keyboard = [[InlineKeyboardButton(f"🚪 {u}", callback_data=f'enter_{i}')] for i, u in admins]
            keyboard.append([InlineKeyboardButton("⬅️ Ortga", callback_data='back_to_main')])
            query.edit_message_text("🚪 Adminni tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            query.edit_message_text("ℹ️ Adminlar yo'q.", reply_markup=back_button())

    elif data.startswith('enter_') and user_id == SUPER_ADMIN_ID:
        admin_id = int(data.split('_')[1])
        context.user_data['viewing_admin'] = admin_id
        query.edit_message_text(f"🏠 Admin xonasi (ID: {admin_id}):", reply_markup=admin_keyboard())

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

        query.edit_message_text(text, reply_markup=keyboard, parse_mode='HTML')
        context.user_data['waiting'] = 'userbot_time'

    elif data == 'userbot_disable_schedule' and user_id == SUPER_ADMIN_ID:
        db.set_setting('userbot_schedule_enabled', 'false')
        query.edit_message_text("✅ Userbot to'xtatish o'chirildi! Userbot 24/7 ishlaydi.", reply_markup=back_button())
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
            text += f"📢 Shaxsiy guruhlar: {private_group_count} ta\n\n"
            text += f"⚙️ Sozlamalar:\n"
            text += f"⏰ Kundalik to'xtatish: {'✅ Yoqilgan' if schedule_enabled == 'true' else '❌ O\'chirilgan'}\n"

            if schedule_enabled == 'true':
                text += f"🌙 To'xtatish: {stop_time}\n🌅 Ishga tushirish: {start_time}\n\n"
            else:
                text += "\n"

            text += f"🕐 Oxirgi tekshiruv: {last_check}\n\n"
            text += "💡 Userbot ishlab turganini tekshirish uchun izlovchi guruhda kalit so'z yozing."

            db.set_setting('userbot_last_check', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Yangilash", callback_data='check_userbot')],
                [InlineKeyboardButton("⬅️ Ortga", callback_data='back_to_main')]
            ])

            query.edit_message_text(text, reply_markup=keyboard)

        except Exception as e:
            query.edit_message_text(f"❌ Xato: {e}", reply_markup=back_button())

    # ========== ADMIN FUNKSIYALARI ==========

    elif data == 'add_keyword':
        context.user_data['waiting'] = 'keyword'
        query.edit_message_text("📝 Kalit so'zni kiriting:", reply_markup=back_button())

    elif data == 'view_keywords':
        admin_id = context.user_data.get('viewing_admin', user_id)
        kws = db.get_keywords(admin_id)
        if kws:
            text = "📋 Kalit so'zlar:\n\n" + "\n".join([f"{i}. {k}" for i, (_, k) in enumerate(kws, 1)]) + f"\n\n💾 Jami: {len(kws)} ta"
            query.edit_message_text(text, reply_markup=back_button())
        else:
            query.edit_message_text("ℹ️ Kalit so'zlar yo'q.", reply_markup=back_button())

    elif data == 'delete_keyword':
        admin_id = context.user_data.get('viewing_admin', user_id)
        kws = db.get_keywords(admin_id)
        if kws:
            keyboard = [[InlineKeyboardButton(f"🗑 {k}", callback_data=f'delkw_{i}')] for i, k in kws]
            keyboard.append([InlineKeyboardButton("⬅️ Ortga", callback_data='back_to_main')])
            query.edit_message_text("🗑 O'chirish uchun tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            query.edit_message_text("ℹ️ Kalit so'zlar yo'q.", reply_markup=back_button())

    elif data.startswith('delkw_'):
        kid = int(data.split('_')[1])
        db.remove_keyword(kid)
        query.edit_message_text("✅ Kalit so'z o'chirildi!", reply_markup=back_button())

    elif data == 'add_private_group':
        context.user_data['waiting'] = 'private_group'
        query.edit_message_text(
            "📝 Shaxsiy guruh ID yoki link yuboring:\n\n💡 ID olish:\n1. Botni guruhga admin qiling\n2. Guruhda /id yuboring\n3. ID yoki linkni bu yerga yuboring",
            reply_markup=back_button()
        )

    elif data == 'view_private_group':
        admin_id = context.user_data.get('viewing_admin', user_id)
        gname = db.get_private_group_name(admin_id)
        if gname:
            query.edit_message_text(f"📢 Shaxsiy guruh: {gname}", reply_markup=back_button())
        else:
            query.edit_message_text("ℹ️ Shaxsiy guruh yo'q.", reply_markup=back_button())

    elif data == 'delete_private_group':
        admin_id = context.user_data.get('viewing_admin', user_id)
        gname = db.get_private_group_name(admin_id)
        if gname:
            keyboard = [[InlineKeyboardButton(f"🗑 {gname}", callback_data=f'delpr_{admin_id}')]]
            keyboard.append([InlineKeyboardButton("⬅️ Ortga", callback_data='back_to_main')])
            query.edit_message_text("🗑 O'chirish uchun shaxsiy guruhni tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            query.edit_message_text("ℹ️ Shaxsiy guruh yo'q.", reply_markup=back_button())

    elif data.startswith('delpr_'):
        admin_id = int(data.split('_')[1])
        db.remove_private_group(admin_id)
        query.edit_message_text("✅ Shaxsiy guruh o'chirildi!", reply_markup=back_button())

    elif data == 'add_search_group':
        admin_id = context.user_data.get('viewing_admin', user_id)
        grps = db.get_search_groups(admin_id)
        context.user_data['waiting'] = 'search_group'
        query.edit_message_text(
            f"📝 Izlovchi guruh ID yoki link yuboring:\n\n📊 Hozirda: {len(grps)}/100 ta\n\n💡 ID olish:\n1. Botni guruhga admin qiling\n2. Guruhda /id yuboring\n3. ID yoki linkni bu yerga yuboring",
            reply_markup=back_button()
        )

    elif data == 'view_search_groups':
        admin_id = context.user_data.get('viewing_admin', user_id)
        grps = db.get_search_groups(admin_id)
        if grps:
            text = "📋 Izlovchi guruhlar:\n\n"
            for i, gname in enumerate([g[1] for g in grps], 1):
                text += f"{i}. {gname}\n"
            text += f"\n💾 Jami: {len(grps)}/100 ta"
            query.edit_message_text(text, reply_markup=back_button())
        else:
            query.edit_message_text("ℹ️ Izlovchi guruhlar yo'q.", reply_markup=back_button())

    elif data == 'delete_search_group':
        admin_id = context.user_data.get('viewing_admin', user_id)
        grps = db.get_search_groups(admin_id)
        if grps:
            keyboard = [[InlineKeyboardButton(f"🗑 {gname}", callback_data=f'delgrp_{rowid}')] for rowid, gname in grps]
            keyboard.append([InlineKeyboardButton("⬅️ Ortga", callback_data='back_to_main')])
            query.edit_message_text("🗑 O'chirish uchun izlovchi guruhni tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            query.edit_message_text("ℹ️ Izlovchi guruhlar yo'q.", reply_markup=back_button())

    elif data.startswith('delgrp_'):
        gid_row = int(data.split('_')[1])
        db.remove_search_group(gid_row)
        query.edit_message_text("✅ Izlovchi guruh o'chirildi!", reply_markup=back_button())

    elif data == 'back_to_main':
        context.user_data.pop('waiting', None)
        if user_id == SUPER_ADMIN_ID:
            context.user_data.pop('viewing_admin', None)
            query.edit_message_text("🔐 Super Admin menyusi:", reply_markup=super_admin_keyboard())
        elif db.is_admin(user_id, SUPER_ADMIN_ID):
            query.edit_message_text("🏠 Admin menyusi:", reply_markup=admin_keyboard())

def handle_text(update: Update, context: CallbackContext):
    """Matn xabarlarni handle qilish"""
    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id
    text = update.message.text.strip()

    waiting = context.user_data.get('waiting')

    if waiting == 'admin_id' and user_id == SUPER_ADMIN_ID:
        try:
            new_id = int(text)
            try:
                chat = context.bot.get_chat(new_id)
                uname = chat.username or chat.first_name or f"User_{new_id}"
            except Exception:
                uname = f"User_{new_id}"

            if db.add_admin(new_id, uname):
                update.message.reply_text(f"✅ Admin qo'shildi!\n\n👤 {uname}\n🆔 {new_id}", reply_markup=back_button())
            else:
                update.message.reply_text("ℹ️ Bu admin mavjud!", reply_markup=back_button())
        except Exception:
            update.message.reply_text("❌ Noto'g'ri ID!", reply_markup=back_button())
        context.user_data.pop('waiting', None)
        return

    # Faqat adminlar davom etishi mumkin
    if not db.is_admin(user_id, SUPER_ADMIN_ID):
        return

    if waiting == 'userbot_time' and user_id == SUPER_ADMIN_ID:
        if text.lower() == 'off':
            db.set_setting('userbot_schedule_enabled', 'false')
            update.message.reply_text("✅ Userbot to'xtatish o'chirildi! 24/7 ishlaydi.", reply_markup=back_button())
        else:
            try:
                times = text.split(':')
                if len(times) == 4:
                    stop_h, stop_m, start_h, start_m = times
                    stop_time = f"{stop_h.zfill(2)}:{stop_m.zfill(2)}"
                    start_time = f"{start_h.zfill(2)}:{start_m.zfill(2)}"

                    db.set_setting('userbot_stop_time', stop_time)
                    db.set_setting('userbot_start_time', start_time)
                    db.set_setting('userbot_schedule_enabled', 'true')

                    update.message.reply_text(
                        f"✅ Vaqt sozlandi!\n\n🌙 To'xtatish: {stop_time}\n🌅 Ishga tushirish: {start_time}",
                        reply_markup=back_button()
                    )
                else:
                    update.message.reply_text("❌ Noto'g'ri format! Misol: 00:00:02:00", reply_markup=back_button())
            except Exception:
                update.message.reply_text("❌ Noto'g'ri format! Misol: 00:00:02:00", reply_markup=back_button())
        context.user_data.pop('waiting', None)

    elif waiting == 'keyword':
        admin_id = context.user_data.get('viewing_admin', user_id)
        db.add_keyword(admin_id, text)
        update.message.reply_text(f"✅ Kalit so'z qo'shildi: {text}", reply_markup=back_button())
        context.user_data.pop('waiting', None)

    elif waiting == 'private_group':
        admin_id = context.user_data.get('viewing_admin', user_id)
        if text.startswith("http"):
            db.add_private_group(admin_id, group_link=text, group_name="Link orqali guruh")
            update.message.reply_text("✅ Shaxsiy guruh qo'shildi: Link orqali guruh", reply_markup=back_button())
        else:
            try:
                gid = int(text)
                try:
                    chat = context.bot.get_chat(gid)
                    gname = chat.title or f"Guruh {gid}"
                except Exception:
                    gname = f"Guruh {gid}"
                db.add_private_group(admin_id, group_id=gid, group_name=gname)
                update.message.reply_text(f"✅ Shaxsiy guruh qo'shildi: {gname}", reply_markup=back_button())
            except Exception:
                update.message.reply_text("❌ Noto'g'ri ID yoki link!", reply_markup=back_button())
        context.user_data.pop('waiting', None)

    elif waiting == 'search_group':
        admin_id = context.user_data.get('viewing_admin', user_id)
        if text.startswith("http"):
            success, message = db.add_search_group(admin_id, SUPER_ADMIN_ID, group_link=text, group_name="Link orqali guruh")
            if success:
                update.message.reply_text(f"✅ {message}: Link orqali guruh", reply_markup=back_button())
            else:
                update.message.reply_text(f"❌ {message}", reply_markup=back_button())
        else:
            try:
                gid = int(text)
                try:
                    chat = context.bot.get_chat(gid)
                    gname = chat.title or f"Guruh {gid}"
                except Exception:
                    gname = f"Guruh {gid}"

                success, message = db.add_search_group(admin_id, SUPER_ADMIN_ID, group_id=gid, group_name=gname)
                if success:
                    update.message.reply_text(f"✅ {message}: {gname}", reply_markup=back_button())
                else:
                    update.message.reply_text(f"❌ {message}", reply_markup=back_button())
            except Exception:
                update.message.reply_text("❌ Noto'g'ri ID yoki link!", reply_markup=back_button())
        context.user_data.pop('waiting', None)

def check_group_message(update: Update, context: CallbackContext):
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
    group_name = update.message.chat.title or "Unknown group"

    # Kalit so'zlarni tekshirish
    matches = db.check_keywords_in_message(group_id, msg_text)

    for match in matches:
        try:
            keyboard = [[InlineKeyboardButton("👤 Profil", url=f"tg://user?id={user_id}")]]
            if match['private_group_id']:
                context.bot.send_message(
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

def error_handler(update: Update, context: CallbackContext):
    """Xatolarni handle qilish"""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Bot ishga tushirish"""
    db.init_db()

    # Default sozlamalarni o'rnatish
    if not db.get_setting('userbot_stop_time'):
        db.set_setting('userbot_stop_time', '00:00')
    if not db.get_setting('userbot_start_time'):
        db.set_setting('userbot_start_time', '02:00')
    if not db.get_setting('userbot_schedule_enabled'):
        db.set_setting('userbot_schedule_enabled', 'true')

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Handlerlarni qo'shish
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("id", get_chat_id))
    dp.add_handler(CallbackQueryHandler(button_callback))
    dp.add_handler(MessageHandler(Filters.text & Filters.private, handle_text))
    dp.add_handler(MessageHandler(Filters.text & Filters.group, check_group_message))
    dp.add_error_handler(error_handler)

    logger.info("🚀 Bot ishga tushmoqda...")

    try:
        updater.start_polling()
        logger.info("✅ Bot ishga tushdi!")
        updater.idle()
    except KeyboardInterrupt:
        logger.info("⛔ Bot to'xtatildi")
    except Exception as e:
        logger.error(f"❌ Xato: {e}")

if __name__ == '__main__':
    main()

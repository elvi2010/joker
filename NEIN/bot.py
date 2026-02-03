import logging
import json
import os
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = "8125618789:AAFl713aRKQMbo2K5_otDZn-Mk9R-s_c2Rc"

class Database:
    class AccountManager:
         def __init__(self, accounts_file="accounts.txt"):
            self.accounts_file = accounts_file
            self.accounts = self.load_accounts()

    
    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except:
                self.data = {"users": {}, "used_accounts": []}
                self.save_data()
        else:
            self.data = {"users": {}, "used_accounts": []}
            self.save_data()
    
    def save_data(self):
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения: {e}")
    
    def user_exists(self, user_id):
        return str(user_id) in self.data["users"]
    
    def add_user(self, user_id, username=""):
        if not self.user_exists(user_id):
            self.data["users"][str(user_id)] = {
                "username": username,
                "free_used": False,
                "referrals": [],
                "referral_count": 0,
                "accounts_received": 0
            }
            self.save_data()
            return True
        return False
    
    def get_user_data(self, user_id):
        return self.data["users"].get(str(user_id))
    
    def mark_free_used(self, user_id):
        if self.user_exists(user_id):
            self.data["users"][str(user_id)]["free_used"] = True
            self.data["users"][str(user_id)]["accounts_received"] += 1
            self.save_data()
    
    def add_referral(self, referrer_id, referral_id):
        referrer_id = str(referrer_id)
        referral_id = str(referral_id)
        
        if (self.user_exists(referrer_id) and 
            referral_id not in self.data["users"][referrer_id]["referrals"] and
            referrer_id != referral_id):
            
            self.data["users"][referrer_id]["referrals"].append(referral_id)
            self.data["users"][referrer_id]["referral_count"] = len(self.data["users"][referrer_id]["referrals"])
            self.save_data()
            return True
        return False
    
    def get_available_accounts_count(self, user_id):
        user_data = self.get_user_data(user_id)
        if not user_data:
            return 0
        
        available = 0
        # Бесплатный аккаунт
        if not user_data["free_used"]:
            available += 1
        
        # Аккаунты за рефералов (за каждых 2 реферала - 1 аккаунт)
        referral_bonus = user_data["referral_count"] // 2
        # Уже полученные аккаунты за рефералов (исключая бесплатный)
        already_received = user_data["accounts_received"] - (1 if user_data["free_used"] else 0)
        
        available += max(0, referral_bonus - already_received)
        return available
    
    def mark_account_received(self, user_id):
        user_data = self.get_user_data(user_id)
        if user_data:
            self.data["users"][str(user_id)]["accounts_received"] += 1
            self.save_data()
    
    def add_used_account(self, account):
        if account not in self.data["used_accounts"]:
            self.data["used_accounts"].append(account)
            self.save_data()
    
    def is_account_used(self, account):
        return account in self.data["used_accounts"]
class AccountManager:
    def _init_(self, accounts_file="accounts.txt"):
        self.accounts_file = accounts_file
        self.accounts = self.load_accounts()
    
    def load_accounts(self):
        try:
            if os.path.exists(self.accounts_file):
                with open(self.accounts_file, 'r', encoding='utf-8') as f:
                    accounts = [line.strip() for line in f if line.strip()]
                logger.info(f"Загружено {len(accounts)} аккаунтов")
                return accounts
            else:
                # Создаем пример файла
                example_accounts = [
                    "user1:password1",
                    "user2:password2", 
                    "user3:password3",
                    "user4:password4",
                    "user5:password5"
                ]
                with open(self.accounts_file, 'w', encoding='utf-8') as f:
                    for account in example_accounts:
                        f.write(account + "\n")
                logger.info(f"Создан файл с примерами аккаунтов")
                return example_accounts
        except Exception as e:
            logger.error(f"Ошибка загрузки аккаунтов: {e}")
            return []
    
    def get_available_account(self):
        try:
            available_accounts = [acc for acc in self.accounts if not db.is_account_used(acc)]
            if available_accounts:
                account = random.choice(available_accounts)
                return account
            return None
        except Exception as e:
            logger.error(f"Ошибка получения аккаунта: {e}")
            return None
    
    def get_total_accounts(self):
        return len(self.accounts)
    
    def get_used_accounts(self):
        return len(db.data.get("used_accounts", []))
    
    def get_available_accounts(self):
        return self.get_total_accounts() - self.get_used_accounts()

# Инициализация
db = Database()
account_manager = AccountManager()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        user_id = user.id
        username = user.username or user.first_name or ""
        
        logger.info(f"Пользователь {user_id} запустил бота")
        
        # Добавляем пользователя если его нет
        db.add_user(user_id, username)
        
        # Обработка реферальной ссылки
        if context.args:
            referrer_id = context.args[0]
            if referrer_id.isdigit():
                referrer_id_int = int(referrer_id)
                if referrer_id_int != user_id:
                    if db.add_referral(referrer_id_int, user_id):
                        logger.info(f"Пользователь {user_id} приглашен по ссылке {referrer_id_int}")
        
        await show_main_menu(update, context)
        
    except Exception as e:
        logger.error(f"Ошибка в start: {e}")
        await update.message.reply_text("❌ Произошла ошибка. Попробуйте еще раз.")

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        user_data = db.get_user_data(user_id)
        
        if not user_data:
            await start(update, context)
            return
        
        keyboard = [
            [InlineKeyboardButton("🎁 Получить аккаунт", callback_data="get_account")],
            [InlineKeyboardButton("👥 Реферальная система", callback_data="referrals")],
            [InlineKeyboardButton("📊 Статистика", callback_data="stats")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        available_user_accounts = db.get_available_accounts_count(user_id)
        
        text = f"""🤖 <b>Бот раздачи аккаунтов</b>

📦 Всего аккаунтов: {account_manager.get_total_accounts()}
🔄 Осталось: {account_manager.get_available_accounts()}

🎁 <b>Ваши возможности:</b>
• Бесплатный: {'✅ Использован' if user_data['free_used'] else '🆓 Доступен'}
• Рефералы: {user_data['referral_count']} чел.
• Доступно к получению: {available_user_accounts} акк.
👥 Приглашайте друзей и получайте больше аккаунтов!"""
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
            
    except Exception as e:
        logger.error(f"Ошибка в show_main_menu: {e}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "get_account":
            await handle_get_account(update, context)
        elif data == "referrals":
            await show_referrals_info(update, context)
        elif data == "stats":
            await show_stats(update, context)
        elif data == "back_to_menu":
            await show_main_menu(update, context)
        elif data == "copy_link":
            await copy_link_handler(update, context)
            
    except Exception as e:
        logger.error(f"Ошибка в button_handler: {e}")

async def handle_get_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        user_id = query.from_user.id
        user_data = db.get_user_data(user_id)
        
        if not user_data:
            await show_main_menu(update, context)
            return
        
        available_count = db.get_available_accounts_count(user_id)
        
        if available_count == 0:
            text = """❌ <b>Нет доступных аккаунтов!</b>

🎁 Бесплатный аккаунт уже использован
👥 Недостаточно рефералов для получения нового

📢 Пригласите друзей чтобы получить больше аккаунтов!"""
            
            keyboard = [
                [InlineKeyboardButton("👥 Пригласить друзей", callback_data="referrals")],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
            return
        
        # Получаем аккаунт
        account = account_manager.get_available_account()
        if not account:
            text = "❌ <b>Все аккаунты разобраны!</b>\nПопробуйте позже."
            await query.edit_message_text(text, parse_mode='HTML')
            return
        
        # Помечаем аккаунт как использованный
        db.add_used_account(account)
        
        # Обновляем данные пользователя
        if not user_data["free_used"]:
            db.mark_free_used(user_id)
        else:
            db.mark_account_received(user_id)
        
        text = f"""✅ <b>Вы получили аккаунт!</b>

📧 <b>Данные аккаунта:</b>
<code>{account}</code>

⚠️ Сохраните эти данные в надежном месте!
⚠️ Рекомендуем сразу сменить пароль!

🎁 Осталось доступных аккаунтов: {db.get_available_accounts_count(user_id)}"""

        keyboard = [[InlineKeyboardButton("🔙 В меню", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Ошибка в handle_get_account: {e}")

async def show_referrals_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        user_id = query.from_user.id
        user_data = db.get_user_data(user_id)
        
        if not user_data:
            await show_main_menu(update, context)
            return
        
        referral_link = f"https://t.me/NEINofficialBot?start={user_id}"
        
        text = f"""👥 <b>Реферальная система</b>

🔗 <b>Ваша реферальная ссылка:</b>
<code>{referral_link}</code>
📊 <b>Статистика:</b>
• Приглашено друзей: {user_data['referral_count']}
• Получено аккаунтов за рефералов: {user_data['accounts_received'] - (1 if user_data['free_used'] else 0)}
• Доступно аккаунтов: {db.get_available_accounts_count(user_id)}

🎯 <b>Условия:</b>
• 1 бесплатный аккаунт при старте
• +1 аккаунт за каждых 2 приглашенных друзей

📢 Поделитесь ссылкой с друзьями!"""

        keyboard = [
            [InlineKeyboardButton("🔗 Скопировать ссылку", callback_data="copy_link")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Ошибка в show_referrals_info: {e}")

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        user_id = query.from_user.id
        user_data = db.get_user_data(user_id)
        
        if not user_data:
            await show_main_menu(update, context)
            return
        
        text = f"""📊 <b>Ваша статистика</b>

👤 <b>Личные данные:</b>
• ID: {user_id}
• Username: @{user_data['username'] or 'не установлен'}

🎁 <b>Аккаунты:</b>
• Бесплатный использован: {'✅ Да' if user_data['free_used'] else '❌ Нет'}
• Всего получено: {user_data['accounts_received']}
• Доступно сейчас: {db.get_available_accounts_count(user_id)}

👥 <b>Рефералы:</b>
• Приглашено: {user_data['referral_count']}
• Список ID: {', '.join(user_data['referrals']) or 'пусто'}

📈 <b>Общая статистика:</b>
• Всего аккаунтов: {account_manager.get_total_accounts()}
• Осталось аккаунтов: {account_manager.get_available_accounts()}
• Использовано: {account_manager.get_used_accounts()}"""

        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Ошибка в show_stats: {e}")

async def copy_link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        user_id = query.from_user.id
        await query.answer("Ссылка скопирована в чат!", show_alert=True)
        
        referral_link = f"https://t.me/NEINofficialBot?start={user_id}"
        await query.message.reply_text(
            f"🔗 <b>Ваша реферальная ссылка:</b>\n<code>{referral_link}</code>\n\n"
            f"📢 Поделитесь этой ссылкой с друзьями!",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Ошибка в copy_link_handler: {e}")

def main():
    try:
        print("🚀 Запуск бота...")
        print(f"📊 Всего аккаунтов: {account_manager.get_total_accounts()}")
        print(f"👥 Пользователей в базе: {len(db.data['users'])}")
        
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(button_handler))
        
        print("✅ Бот запущен и готов к работе!")
        print("🛑 Для остановки нажмите Ctrl+C")
        
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
        print(f"❌ Ошибка: {e}")

if __name__ == "_main_":
    main()
 
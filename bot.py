import json
import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from datetime import datetime, timedelta
import re

API_TOKEN = '8203398409:AAEZjF_apz2fbvDkJGDvWn2SdI-kNMQUGUQ'
ADMIN_IDS = [5282167584, 8351236421]
SUPPORT_GROUP_ID = -5057766805
REVIEWS_CHANNEL_ID = '-1003658648586'
BOT_USERNAME = 'Donatka_uzBot'

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

DATA_FILE = 'donat.json'
PAYMENT_METHODS_FILE = 'payment_methods.json'
TEMPLATES_FILE = 'templates.json'

DEFAULT_SETTINGS = {
    'exchange_rates': {'standoff': 125, 'roblox': 149, 'tgstar': 260},
    'min_purchase': 90000, 'max_purchase': 10000000,
    'min_withdraw': {'standoff': 50, 'roblox': 500, 'tgstar': 50},
    'max_withdraw': {'standoff': 10000, 'roblox': 100000, 'tgstar': 10000},
    'withdraw_multiplier': 1.25
}

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if 'settings' not in data:
                data['settings'] = DEFAULT_SETTINGS
            return data
    return {
        'users': {},
        'support_tickets': {},
        'promocodes': {},
        'withdraw_requests': {},
        'purchase_requests': {},
        'reviews': {},
        'referral_settings': {'standoff_percent': 10, 'roblox_percent': 10, 'tgstar_percent': 10},
        'settings': DEFAULT_SETTINGS,
        'stats': {'total_users': 0, 'total_withdraw_standoff': 0, 'total_withdraw_roblox': 0, 'total_withdraw_tgstar': 0, 'total_reviews': 0, 'total_purchases': 0, 'total_purchases_amount': 0}
    }

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_payment_methods():
    if os.path.exists(PAYMENT_METHODS_FILE):
        with open(PAYMENT_METHODS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'methods': [], 'next_id': 0}

def save_payment_methods(data):
    with open(PAYMENT_METHODS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_templates():
    if os.path.exists(TEMPLATES_FILE):
        with open(TEMPLATES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'templates': [], 'next_id': 1}

def save_templates(data):
    with open(TEMPLATES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_template_by_id(template_id):
    templates_data = load_templates()
    for template in templates_data['templates']:
        if template['id'] == template_id:
            return template
    return None

def has_active_purchase_request(user_id):
    data = load_data()
    purchase_requests = data.get('purchase_requests', {})
    for request_id, request_data in purchase_requests.items():
        if request_data.get('user_id') == str(user_id) and request_data.get('status') == 'pending':
            return True
    return False

def has_active_withdraw_request(user_id):
    data = load_data()
    withdraw_requests = data.get('withdraw_requests', {})
    for request_id, request_data in withdraw_requests.items():
        if request_data.get('user_id') == str(user_id) and request_data.get('status') == 'pending':
            return True
    return False

def calculate_period_stats(data, game=None):
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    week_ago = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    month_ago = (now - timedelta(days=30)).strftime("%Y-%m-%d")
    
    total_users = 0
    users_today = 0
    users_week = 0
    users_month = 0
    
    total_purchases = 0
    purchases_today = 0
    purchases_week = 0
    purchases_month = 0
    total_purchase_amount = 0
    purchase_amount_today = 0
    purchase_amount_week = 0
    purchase_amount_month = 0
    
    total_withdraw = 0
    withdraw_today = 0
    withdraw_week = 0
    withdraw_month = 0
    
    total_reviews = 0
    
    active_users_today = set()
    
    for user_id, user_data in data['users'].items():
        reg_date = user_data.get('registration_date', '').split()[0]
        
        total_users += 1
        
        if reg_date == today:
            users_today += 1
        if reg_date >= week_ago:
            users_week += 1
        if reg_date >= month_ago:
            users_month += 1
        
        if user_data.get('balance_standoff', 0) > 0 or user_data.get('balance_roblox', 0) > 0 or user_data.get('balance_tgstar', 0) > 0:
            active_users_today.add(user_id)
    
    for purchase_id, purchase_data in data.get('purchase_requests', {}).items():
        purchase_game = purchase_data.get('game')
        status = purchase_data.get('status')
        
        if game and game != 'all' and purchase_game != game:
            continue
        
        if status == 'completed':
            timestamp = purchase_data.get('timestamp', '').split()[0]
            amount_uzs = purchase_data.get('amount_uzs', 0)
            
            total_purchases += 1
            total_purchase_amount += amount_uzs
            
            if timestamp == today:
                purchases_today += 1
                purchase_amount_today += amount_uzs
            if timestamp >= week_ago:
                purchases_week += 1
                purchase_amount_week += amount_uzs
            if timestamp >= month_ago:
                purchases_month += 1
                purchase_amount_month += amount_uzs
    
    for withdraw_id, withdraw_data in data.get('withdraw_requests', {}).items():
        withdraw_game = withdraw_data.get('game')
        status = withdraw_data.get('status')
        
        if game and game != 'all' and withdraw_game != game:
            continue
        
        if status == 'completed':
            timestamp = withdraw_data.get('timestamp', '').split()[0]
            amount = withdraw_data.get('amount', 0)
            
            total_withdraw += amount
            
            if timestamp == today:
                withdraw_today += amount
            if timestamp >= week_ago:
                withdraw_week += amount
            if timestamp >= month_ago:
                withdraw_month += amount
    
    for review_id, review_data in data.get('reviews', {}).items():
        review_game = review_data.get('game')
        status = review_data.get('status')
        
        if game and game != 'all' and review_game != game:
            continue
        
        if status == 'published':
            total_reviews += 1
    
    total_balance_standoff = sum(user.get('balance_standoff', 0) for user in data['users'].values())
    total_balance_roblox = sum(user.get('balance_roblox', 0) for user in data['users'].values())
    total_balance_tgstar = sum(user.get('balance_tgstar', 0) for user in data['users'].values())
    
    banned_users = sum(1 for user in data['users'].values() if user.get('banned', False))
    
    return {
        'total_users': total_users,
        'users_today': users_today,
        'users_week': users_week,
        'users_month': users_month,
        'total_purchases': total_purchases,
        'purchases_today': purchases_today,
        'purchases_week': purchases_week,
        'purchases_month': purchases_month,
        'total_purchase_amount': total_purchase_amount,
        'purchase_amount_today': purchase_amount_today,
        'purchase_amount_week': purchase_amount_week,
        'purchase_amount_month': purchase_amount_month,
        'total_withdraw': total_withdraw,
        'withdraw_today': withdraw_today,
        'withdraw_week': withdraw_week,
        'withdraw_month': withdraw_month,
        'total_reviews': total_reviews,
        'active_users_today': len(active_users_today),
        'banned_users': banned_users,
        'total_balance_standoff': total_balance_standoff,
        'total_balance_roblox': total_balance_roblox,
        'total_balance_tgstar': total_balance_tgstar
    }

class AdminStates(StatesGroup):
    waiting_user_id = State()
    waiting_user_balance = State()
    waiting_user_message = State()
    waiting_mailing = State()
    waiting_promocode_name = State()
    waiting_promocode_bonus = State()
    waiting_promocode_activations = State()
    waiting_delete_promocode = State()
    waiting_ref_percent = State()
    waiting_exchange_rate = State()
    waiting_payment_method_bank = State()
    waiting_payment_method_recipient = State()
    waiting_payment_method_card = State()
    waiting_payment_method_phone = State()
    waiting_delete_payment_method = State()
    waiting_min_max_value = State()
    waiting_admin_reply = State()
    waiting_payment_method_game = State()
    waiting_template_name = State()
    waiting_template_text = State()
    waiting_template_category = State()

class UserStates(StatesGroup):
    waiting_promocode = State()
    waiting_withdraw_amount = State()
    waiting_withdraw_screenshot = State()
    waiting_withdraw_roblox_method = State()
    waiting_withdraw_roblox_login = State()
    waiting_withdraw_roblox_gamepass = State()
    waiting_tgstar_username = State()
    waiting_review_rating = State()
    waiting_review_text = State()
    waiting_review_screenshot = State()
    waiting_purchase_amount = State()
    waiting_purchase_screenshot = State()
    waiting_payment_method_choice = State()
    waiting_calculator_type = State()
    waiting_calculator_value = State()

class SupportStates(StatesGroup):
    waiting_for_question = State()

def generate_id(data, key):
    max_id = 0
    for req_id in data.get(key, {}).keys():
        try:
            max_id = max(max_id, int(req_id))
        except:
            pass
    return max_id + 1

def get_user_number(data, user_id):
    user_ids = list(data['users'].keys())
    return user_ids.index(user_id) + 1 if user_id in user_ids else 0

def main_menu_reply_keyboard():
    return ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("🏠 Главное меню"))

def games_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🎮 Standoff 2", callback_data="game_standoff"),
        InlineKeyboardButton("🔲 Roblox", callback_data="game_roblox"),
        InlineKeyboardButton("⭐️ Tg star", callback_data="game_tgstar")
    )
    return keyboard

def standoff_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(KeyboardButton("💰 Купить голду"), KeyboardButton("🍯 Вывести голду"))
    keyboard.add(KeyboardButton("🆔 Профиль"), KeyboardButton("📖 Поддержка"))
    keyboard.add(KeyboardButton("🔢 Посчитать"), KeyboardButton("🎮 Сменить игру"))
    return keyboard

def roblox_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(KeyboardButton("💰 Купить робаксы"), KeyboardButton("⭐ Вывести робаксы"))
    keyboard.add(KeyboardButton("🆔 Профиль"), KeyboardButton("📖 Поддержка"))
    keyboard.add(KeyboardButton("🔢 Посчитать"), KeyboardButton("🎮 Сменить игру"))
    return keyboard

def tgstar_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(KeyboardButton("💰 Купить звезды"), KeyboardButton("⭐ Вывести звезды"))
    keyboard.add(KeyboardButton("🆔 Профиль"), KeyboardButton("📖 Поддержка"))
    keyboard.add(KeyboardButton("🎮 Сменить игру"), KeyboardButton("⭐️ TG Premium"))
    return keyboard

def admin_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📨 Рассылка", callback_data="admin_mailing"),
        InlineKeyboardButton("⚙️ Настройки", callback_data="admin_settings")
    )
    keyboard.add(
        InlineKeyboardButton("🎁 Промокоды", callback_data="admin_promocodes"),
        InlineKeyboardButton("💵 Оплата", callback_data="admin_payment")
    )
    keyboard.add(
        InlineKeyboardButton("🔎 Найти юзера", callback_data="admin_find_user"),
        InlineKeyboardButton("🗒 Заявки", callback_data="admin_requests")
    )
    keyboard.add(
        InlineKeyboardButton("📝 Шаблоны", callback_data="admin_templates"),
        InlineKeyboardButton("🔙 Главное меню", callback_data="admin_back_to_main")
    )
    return keyboard

def admin_settings_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        InlineKeyboardButton("🏆 Топы", callback_data="admin_tops")
    )
    keyboard.add(
        InlineKeyboardButton("💌 Реф.Система", callback_data="ref_system"),
        InlineKeyboardButton("💱 Курс", callback_data="exchange_rates")
    )
    keyboard.add(
        InlineKeyboardButton("⚡️ Лимиты", callback_data="admin_limits"),
        InlineKeyboardButton("🔙 Назад", callback_data="admin_back")
    )
    return keyboard

def rating_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=5)
    for i in range(1, 6):
        keyboard.insert(InlineKeyboardButton(str(i), callback_data=f"rating_{i}"))
    return keyboard

def withdraw_decision_keyboard(request_id):
    return InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("✅ Принять", callback_data=f"withdraw_accept_{request_id}"),
        InlineKeyboardButton("❌ Отклонить", callback_data=f"withdraw_reject_{request_id}")
    )

def purchase_decision_keyboard(request_id):
    return InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("✅ Принять", callback_data=f"purchase_accept_{request_id}"),
        InlineKeyboardButton("❌ Отклонить", callback_data=f"purchase_reject_{request_id}")
    )

def review_decision_keyboard(review_id):
    return InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("✅ Выложить", callback_data=f"review_publish_{review_id}"),
        InlineKeyboardButton("❌ Отклонить", callback_data=f"review_reject_{review_id}")
    )

def calculator_type_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("💰 UZS → Игра", callback_data="calc_to_game"),
        InlineKeyboardButton("🎮 Игра → UZS", callback_data="calc_to_uzs")
    )
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="calc_back"))
    return keyboard

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    if message.chat.id == SUPPORT_GROUP_ID:
        return
    
    user_id = str(message.from_user.id)
    data = load_data()
    
    if user_id in data['users']:
        user_data = data['users'][user_id]
        if user_data.get('banned', False):
            await message.answer("🚫 <b>Вы забанены.</b>", parse_mode="HTML")
            return
        await show_game_menu(message.chat.id, user_data.get('game', 'standoff'), message.from_user.username or message.from_user.first_name)
    else:
        ref_user_id = None
        if len(message.text.split()) > 1:
            ref_param = message.text.split()[1]
            if ref_param.startswith('ref'):
                ref_user_id = ref_param[3:]
        
        user_data = {
            'username': message.from_user.username or message.from_user.first_name,
            'game': None,
            'balance_standoff': 0,
            'balance_roblox': 0,
            'balance_tgstar': 0,
            'registration_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'is_active': True,
            'activated_promocodes': [],
            'referrer_id': ref_user_id,
            'referrals': [],
            'total_earned_standoff': 0,
            'total_earned_roblox': 0,
            'total_earned_tgstar': 0,
            'total_ref_earned_standoff': 0,
            'total_ref_earned_roblox': 0,
            'total_ref_earned_tgstar': 0,
            'banned': False
        }
        
        if ref_user_id and ref_user_id in data['users'] and ref_user_id != user_id:
            if 'referrals' not in data['users'][ref_user_id]:
                data['users'][ref_user_id]['referrals'] = []
            data['users'][ref_user_id]['referrals'].append(user_id)
            user_data['referrer_id'] = ref_user_id
        
        data['users'][user_id] = user_data
        data['stats']['total_users'] = len(data['users'])
        save_data(data)
        
        await message.answer("<b>👋 Добро пожаловать!</b>\n\nЗдесь ты можешь быстро и безопасно оформить донат на:\n<b>🎮 Roblox</b>\n<b>🔫 Standoff 2</b>\n<b>⭐ Telegram Stars</b>\n<b>💎 Telegram Premium</b>\n\nВыбирай нужный сервис, следуй инструкциям — и всё готово!\nЕсли возникнут вопросы, бот подскажет на каждом шаге 😉\nПриятных покупок и спасибо за поддержку! ❤️", parse_mode="HTML", reply_markup=games_keyboard())

async def show_game_menu(chat_id, game_type, username):
    keyboards = {'standoff': standoff_keyboard(), 'roblox': roblox_keyboard(), 'tgstar': tgstar_keyboard()}
    await bot.send_message(chat_id, "<b>👋 Добро пожаловать!</b>\n\nЗдесь ты можешь быстро и безопасно оформить донат на:\n<b>🎮 Roblox</b>\n<b>🔫 Standoff 2</b>\n<b>⭐ Telegram Stars</b>\n<b>💎 Telegram Premium</b>\n\nВыбирай нужный сервис, следуй инструкциям — и всё готово!\nЕсли возникнут вопросы, бот подскажет на каждом шаге 😉\nПриятных покупок и спасибо за поддержку! ❤️", parse_mode="HTML", reply_markup=keyboards[game_type])

@dp.message_handler(lambda message: message.text == "🏠 Главное меню", state='*')
async def main_menu_handler(message: types.Message, state: FSMContext=None):
    if message.chat.id == SUPPORT_GROUP_ID:
        return
    
    if state:
        current_state = await state.get_state()
        if current_state is not None:
            await state.finish()
    
    user_id = str(message.from_user.id)
    data = load_data()
    
    try:
        await message.delete()
    except:
        pass
    
    if user_id in data['users']:
        user_data = data['users'][user_id]
        if user_data.get('banned', False):
            await message.answer("🚫 <b>Вы забанены.</b>", parse_mode="HTML")
            return
        await show_game_menu(message.chat.id, user_data.get('game', 'standoff'), user_data['username'])
    else:
        await message.answer("👇 Выберите игру:", parse_mode="HTML", reply_markup=games_keyboard())

@dp.callback_query_handler(lambda c: c.data.startswith('game_'))
async def process_game_selection(callback_query: types.CallbackQuery):
    if callback_query.message.chat.id == SUPPORT_GROUP_ID:
        await callback_query.answer()
        return
    
    user_id = str(callback_query.from_user.id)
    game_type = callback_query.data.split('_')[1]
    data = load_data()
    
    if user_id not in data['users']:
        data['users'][user_id] = {
            'username': callback_query.from_user.username or callback_query.from_user.first_name,
            'game': game_type,
            'balance_standoff': 0,
            'balance_roblox': 0,
            'balance_tgstar': 0,
            'registration_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'is_active': True,
            'activated_promocodes': [],
            'referrer_id': None,
            'referrals': [],
            'total_earned_standoff': 0,
            'total_earned_roblox': 0,
            'total_earned_tgstar': 0,
            'total_ref_earned_standoff': 0,
            'total_ref_earned_roblox': 0,
            'total_ref_earned_tgstar': 0,
            'banned': False
        }
    else:
        data['users'][user_id]['game'] = game_type
    
    save_data(data)
    
    try:
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    except:
        pass
    
    await show_game_menu(callback_query.message.chat.id, game_type, callback_query.from_user.username or callback_query.from_user.first_name)
    await callback_query.answer()

@dp.message_handler(lambda message: message.text == "🆔 Профиль")
async def process_profile_button(message: types.Message):
    if message.chat.id == SUPPORT_GROUP_ID:
        return
    
    user_id = str(message.from_user.id)
    data = load_data()
    
    if user_id not in data['users']:
        await message.answer("❌ Пользователь не найден.", parse_mode="HTML")
        return
    
    user_data = data['users'][user_id]
    if user_data.get('banned', False):
        await message.answer("🚫 <b>Вы забанены.</b>", parse_mode="HTML")
        return
    
    current_game = user_data.get('game', 'standoff')
    game_info = {
        'standoff': {'currency': 'Gold', 'balance': user_data.get('balance_standoff', 0), 'emoji': '🍯'},
        'roblox': {'currency': 'Robux', 'balance': user_data.get('balance_roblox', 0), 'emoji': '💰'},
        'tgstar': {'currency': 'Stars', 'balance': user_data.get('balance_tgstar', 0), 'emoji': '⭐️'}
    }
    info = game_info[current_game]
    
    text = f"✉️ <b>Никнейм:</b> @{user_data.get('username', 'Без имени')}\n"
    text += f"💎 <b>UID:</b> {message.from_user.id}\n"
    text += f"🆔 <b>Айди (в боте):</b> {get_user_number(data, user_id)}\n"
    text += f"{info['emoji']} <b>Баланс:</b> {info['balance']} {info['currency']}\n\n"
    text += f"📎 <b>Реф.ссылка:</b>\n<code>https://t.me/{BOT_USERNAME}?start=ref{user_id}</code>\n"
    text += f"🫂 <b>Рефералов:</b> {len(user_data.get('referrals', []))}\n"
    
    if user_data.get('total_ref_earned_standoff', 0) > 0 or user_data.get('total_ref_earned_roblox', 0) > 0 or user_data.get('total_ref_earned_tgstar', 0) > 0:
        text += f"\n💰 <b>Заработано с рефералов:</b>\n"
        if user_data['total_ref_earned_standoff'] > 0:
            text += f"• Standoff 2: {user_data['total_ref_earned_standoff']} Gold\n"
        if user_data['total_ref_earned_roblox'] > 0:
            text += f"• Roblox: {user_data['total_ref_earned_roblox']} Robux\n"
        if user_data['total_ref_earned_tgstar'] > 0:
            text += f"• TG Star: {user_data['total_ref_earned_tgstar']} Stars"
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🎁 Промокод", callback_data="activate_promocode"))
    
    try:
        await message.delete()
    except:
        pass
    
    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)

@dp.message_handler(lambda message: message.text in ["🍯 Вывести голду", "⭐ Вывести робаксы", "⭐ Вывести звезды"])
async def process_withdraw_button(message: types.Message):
    if message.chat.id == SUPPORT_GROUP_ID:
        return
    
    user_id = str(message.from_user.id)
    data = load_data()
    
    if user_id not in data['users']:
        await message.answer("❌ Пользователь не найден.", parse_mode="HTML")
        return
    
    user_data = data['users'][user_id]
    if user_data.get('banned', False):
        await message.answer("🚫 <b>Вы забанены.</b>", parse_mode="HTML")
        return
    
    if has_active_withdraw_request(message.from_user.id):
        await message.answer(
            "🕑 <b>Подождите, вашу заявку на вывод проверяют.</b>\n\nПосле обработки, вы получите уведомление.",
            parse_mode="HTML",
            reply_markup=main_menu_reply_keyboard()
        )
        return
    
    games = {"🍯 Вывести голду": 'standoff', "⭐ Вывести робаксы": 'roblox', "⭐ Вывести звезды": 'tgstar'}
    game = games[message.text]
    
    if user_data.get('game') != game:
        game_names = {'standoff': 'Standoff 2', 'roblox': 'Roblox', 'tgstar': 'TG Star'}
        await message.answer(f"❌ Функция только для {game_names[game]}.", parse_mode="HTML")
        return
    
    balance = user_data.get(f'balance_{game}', 0)
    min_withdraw = data['settings']['min_withdraw'][game]
    
    if balance < min_withdraw:
        await message.answer(f"❌ Мин. сумма вывода: {min_withdraw}\n💰 Баланс: {balance}", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        return
    
    try:
        await message.delete()
    except:
        pass
    
    currency = {'standoff': 'Gold', 'roblox': 'Robux', 'tgstar': 'Stars'}[game]
    await message.answer(f"🎁 <b>Напиши сумму {currency.lower()} для вывода:</b>\n\n💰 <b>Баланс:</b> {balance} {currency}\n📊 <b>Мин. сумма:</b> {min_withdraw} {currency}", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
    await UserStates.waiting_withdraw_amount.set()
    await dp.current_state(chat=message.chat.id, user=user_id).update_data(game=game, currency=currency, balance_field=f'balance_{game}')

@dp.message_handler(state=UserStates.waiting_withdraw_amount)
async def process_withdraw_amount(message: types.Message, state: FSMContext):
    if message.text == "🏠 Главное меню":
        await state.finish()
        data = load_data()
        user_id = str(message.from_user.id)
        user_data = data['users'].get(user_id, {})
        await show_game_menu(message.chat.id, user_data.get('game', 'standoff'), user_data['username'])
        return
    
    try:
        amount = int(message.text)
    except:
        await message.answer("❌ Введите число.", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        return
    
    user_id = str(message.from_user.id)
    data = load_data()
    
    if user_id not in data['users']:
        await message.answer("❌ Пользователь не найден.", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        await state.finish()
        return
    
    state_data = await state.get_data()
    game = state_data.get('game')
    currency = state_data.get('currency')
    balance_field = state_data.get('balance_field')
    
    user_data = data['users'][user_id]
    balance = user_data.get(balance_field, 0)
    min_withdraw = data['settings']['min_withdraw'][game]
    max_withdraw = data['settings']['max_withdraw'][game]
    
    if amount < min_withdraw:
        await message.answer(f"❌ Мин. сумма: {min_withdraw} {currency}", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        return
    if amount > max_withdraw:
        await message.answer(f"❌ Макс. сумма: {max_withdraw} {currency}", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        return
    if amount > balance:
        await message.answer(f"❌ Недостаточно средств.\n💰 Баланс: {balance} {currency}", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        return
    
    await state.update_data(amount=amount)
    
    try:
        await message.delete()
    except:
        pass
    
    if game == 'standoff':
        market_price = round(amount * data['settings']['withdraw_multiplier'], 2)
        await state.update_data(market_price=market_price)
        await message.answer(f"✨ Отлично! <b>Теперь поставьте скин SM1014 'Falling Leaves' за {market_price} G для получения {amount}G.</b>\n📝 <b>Сделайте скриншот и отправьте сюда, в чат:</b>", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        await UserStates.waiting_withdraw_screenshot.set()
    elif game == 'roblox':
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            InlineKeyboardButton("🎮 GamePass", callback_data="roblox_gamepass"),
            InlineKeyboardButton("🔙 Назад", callback_data="roblox_back")
        )
        await message.answer("👇 <b>Выберите способ вывода:</b>", parse_mode="HTML", reply_markup=keyboard)
        await UserStates.waiting_withdraw_roblox_method.set()
    elif game == 'tgstar':
        current_username = message.from_user.username or message.from_user.first_name
        await message.answer("✍️ <b>Напиши юзернейм для отправки звезд:</b>\n<i>Обязательно через @</i>", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        await UserStates.waiting_tgstar_username.set()

@dp.message_handler(content_types=['photo'], state=UserStates.waiting_withdraw_screenshot)
async def process_withdraw_screenshot(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    data = load_data()
    
    if user_id not in data['users']:
        await message.answer("❌ Пользователь не найден.", parse_mode="HTML")
        await state.finish()
        return
    
    state_data = await state.get_data()
    amount = state_data.get('amount')
    game = state_data.get('game')
    currency = state_data.get('currency')
    balance_field = state_data.get('balance_field')
    market_price = state_data.get('market_price')
    
    if not amount:
        await message.answer("❌ Ошибка данных.", parse_mode="HTML")
        await state.finish()
        return
    
    user_data = data['users'][user_id]
    if amount > user_data.get(balance_field, 0):
        await message.answer("❌ Недостаточно средств.", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        await state.finish()
        return
    
    user_data[balance_field] -= amount
    
    withdraw_id = generate_id(data, 'withdraw_requests')
    
    withdraw_data = {
        'user_id': user_id,
        'username': message.from_user.username or message.from_user.first_name,
        'amount': amount,
        'game': game,
        'currency': currency,
        'status': 'pending',
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'screenshot_file_id': message.photo[-1].file_id
    }
    
    if game == 'standoff':
        withdraw_data['market_price'] = market_price
    
    if 'withdraw_requests' not in data:
        data['withdraw_requests'] = {}
    data['withdraw_requests'][str(withdraw_id)] = withdraw_data
    
    stats_key = f"total_withdraw_{game}"
    if stats_key not in data['stats']:
        data['stats'][stats_key] = 0
    data['stats'][stats_key] += amount
    
    save_data(data)
    
    try:
        await message.delete()
    except:
        pass
    
    await message.answer("✉️ <b>Заявка отправлена на проверку.</b>", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
    
    try:
        user_number = get_user_number(data, user_id)
        caption = f"📋 <b>Заявка на вывод #{withdraw_id}</b> <code>({user_number})</code>\n\n"
        caption += f"👤 <b>Пользователь:</b> @{message.from_user.username or message.from_user.first_name}\n"
        caption += f"🆔 <b>ID:</b> <code>{user_id}</code>\n\n"
        caption += f"🎮 <b>Игра:</b> {'Standoff 2' if game == 'standoff' else 'Roblox' if game == 'roblox' else 'TG Star'}\n"
        caption += f"💰 <b>Сумма:</b> {amount} {currency}\n"
        if game == 'standoff':
            caption += f"🏷️ <b>Цена на рынке:</b> {market_price} G\n\n"
        caption += f"⏰ <b>Время создания:</b> {data['withdraw_requests'][str(withdraw_id)]['timestamp']}\n\n"
        
        await bot.send_photo(SUPPORT_GROUP_ID, message.photo[-1].file_id, caption=caption, parse_mode="HTML", reply_markup=withdraw_decision_keyboard(withdraw_id))
    except Exception as e:
        print(f"Ошибка отправки: {e}")
    
    await state.finish()

@dp.callback_query_handler(lambda c: c.data in ['roblox_gamepass', 'roblox_back'], state=UserStates.waiting_withdraw_roblox_method)
async def process_roblox_method(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data == 'roblox_back':
        await state.finish()
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
        data = load_data()
        user_id = str(callback_query.from_user.id)
        user_data = data['users'].get(user_id, {})
        await show_game_menu(callback_query.message.chat.id, user_data.get('game', 'standoff'), user_data['username'])
        return
    
    await state.update_data(roblox_method='gamepass')
    
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    
    gamepass_text = "✍️ <b>Пришлите мне свой game pass.</b>\n\n"
    gamepass_text += "✉️ <b>Как создать game pass?</b>\n"
    gamepass_text += "1. Посмотрите видео\n"
    gamepass_text += "2. Выключите региональную цену - это можно сделать под управлением цены!\n"
    gamepass_text += "3. Скопируйте ID от пасса и скиньте мне!\n\n"
    gamepass_text += "🎮 <b>Введите ID GamePass:</b>"
    
    await bot.send_message(callback_query.message.chat.id, gamepass_text, parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
    await UserStates.waiting_withdraw_roblox_gamepass.set()
    
    await callback_query.answer()

@dp.message_handler(state=UserStates.waiting_withdraw_roblox_gamepass)
async def process_roblox_gamepass(message: types.Message, state: FSMContext):
    if message.text == "🏠 Главное меню":
        await state.finish()
        data = load_data()
        user_id = str(message.from_user.id)
        user_data = data['users'].get(user_id, {})
        await show_game_menu(message.chat.id, user_data.get('game', 'standoff'), user_data['username'])
        return
    
    gamepass_id = message.text.strip()
    if not gamepass_id.isdigit():
        await message.answer("❌ ID должен быть числом.", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        return
    
    await state.update_data(roblox_gamepass=gamepass_id)
    await message.answer("🔐 <b>Введите логин:пароль от аккаунта Roblox:</b>\n\n<i>Пример: username123:password123</i>", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
    await UserStates.waiting_withdraw_roblox_login.set()

@dp.message_handler(state=UserStates.waiting_withdraw_roblox_login)
async def process_roblox_login(message: types.Message, state: FSMContext):
    if message.text == "🏠 Главное меню":
        await state.finish()
        data = load_data()
        user_id = str(message.from_user.id)
        user_data = data['users'].get(user_id, {})
        await show_game_menu(message.chat.id, user_data.get('game', 'standoff'), user_data['username'])
        return
    
    credentials = message.text.strip()
    if ':' not in credentials:
        await message.answer("❌ Формат: логин:пароль", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        return
    
    await state.update_data(roblox_credentials=credentials)
    await process_roblox_withdraw_final(message, state)

async def process_roblox_withdraw_final(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    data = load_data()
    
    state_data = await state.get_data()
    amount = state_data.get('amount')
    game = state_data.get('game')
    currency = state_data.get('currency')
    balance_field = state_data.get('balance_field')
    method = state_data.get('roblox_method', 'gamepass')
    gamepass_id = state_data.get('roblox_gamepass')
    credentials = state_data.get('roblox_credentials')
    
    if not amount:
        await message.answer("❌ Ошибка данных.", parse_mode="HTML")
        await state.finish()
        return
    
    user_data = data['users'][user_id]
    if amount > user_data.get(balance_field, 0):
        await message.answer("❌ Недостаточно средств.", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        await state.finish()
        return
    
    user_data[balance_field] -= amount
    
    withdraw_id = generate_id(data, 'withdraw_requests')
    
    withdraw_data = {
        'user_id': user_id,
        'username': message.from_user.username or message.from_user.first_name,
        'amount': amount,
        'game': game,
        'currency': currency,
        'status': 'pending',
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'method': method,
        'gamepass_id': gamepass_id,
        'credentials': credentials
    }
    
    if 'withdraw_requests' not in data:
        data['withdraw_requests'] = {}
    data['withdraw_requests'][str(withdraw_id)] = withdraw_data
    
    data['stats']['total_withdraw_roblox'] += amount
    save_data(data)
    
    try:
        await message.delete()
    except:
        pass
    
    await message.answer("✉️ <b>Заявка отправлена на проверку.</b>", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
    
    try:
        user_number = get_user_number(data, user_id)
        
        login_pass = credentials.split(':')
        login = login_pass[0] if len(login_pass) > 0 else ''
        password = login_pass[1] if len(login_pass) > 1 else ''
        
        caption = f"📋 <b>Заявка на вывод #{withdraw_id}</b> <code>({user_number})</code>\n\n"
        caption += f"👤 <b>Пользователь:</b> @{message.from_user.username or message.from_user.first_name}\n"
        caption += f"🆔 <b>ID:</b> <code>{user_id}</code>\n\n"
        caption += f"🎮 <b>Игра:</b> Roblox\n"
        caption += f"💰 <b>Сумма:</b> {amount} {currency}\n"
        caption += f"🆔 <b>Айди GamePass:</b> <code>{gamepass_id}</code>\n\n"
        caption += f"👤 <b>Логин:</b> <code>{login}</code>\n"
        caption += f"🔐 <b>Пароль:</b> <code>{password}</code>\n"
        caption += f"⏰ <b>Время создания:</b> {data['withdraw_requests'][str(withdraw_id)]['timestamp']}\n\n"
        
        await bot.send_message(SUPPORT_GROUP_ID, caption, parse_mode="HTML", reply_markup=withdraw_decision_keyboard(withdraw_id))
    except Exception as e:
        print(f"Ошибка отправки: {e}")
    
    await state.finish()

@dp.message_handler(state=UserStates.waiting_tgstar_username)
async def process_tgstar_username(message: types.Message, state: FSMContext):
    if message.text == "🏠 Главное меню":
        await state.finish()
        data = load_data()
        user_id = str(message.from_user.id)
        user_data = data['users'].get(user_id, {})
        await show_game_menu(message.chat.id, user_data.get('game', 'standoff'), user_data['username'])
        return
    
    username_input = message.text.strip()
    
    if not username_input.startswith('@'):
        await message.answer("❌ <b>Юзернейм должен начинаться с @</b>\nПример: @username", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        return
    
    state_data = await state.get_data()
    amount = state_data.get('amount')
    game = state_data.get('game')
    currency = state_data.get('currency')
    balance_field = state_data.get('balance_field')
    
    if not amount:
        await message.answer("❌ Ошибка данных.", parse_mode="HTML")
        await state.finish()
        return
    
    user_id = str(message.from_user.id)
    data = load_data()
    
    if user_id not in data['users']:
        await message.answer("❌ Пользователь не найден.", parse_mode="HTML")
        await state.finish()
        return
    
    user_data = data['users'][user_id]
    if amount > user_data.get(balance_field, 0):
        await message.answer("❌ Недостаточно средств.", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        await state.finish()
        return
    
    user_data[balance_field] -= amount
    
    withdraw_id = generate_id(data, 'withdraw_requests')
    
    if 'withdraw_requests' not in data:
        data['withdraw_requests'] = {}
    
    data['withdraw_requests'][str(withdraw_id)] = {
        'user_id': user_id,
        'username': message.from_user.username or message.from_user.first_name,
        'amount': amount,
        'receiver_username': username_input,
        'game': game,
        'currency': currency,
        'status': 'pending',
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    data['stats']['total_withdraw_tgstar'] += amount
    save_data(data)
    
    try:
        await message.delete()
    except:
        pass
    
    await message.answer(f"✉️ <b>Заявка отправлена.</b>\n💰 {amount} Stars\n📨 {username_input}", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
    
    try:
        user_number = get_user_number(data, user_id)
        caption = f"📋 <b>Заявка на вывод #{withdraw_id}</b> <code>({user_number})</code>\n\n"
        caption += f"👤 <b>Пользователь:</b> @{message.from_user.username or message.from_user.first_name}\n"
        caption += f"🆔 <b>ID:</b> <code>{user_id}</code>\n\n"
        caption += f"🎮 <b>Игра:</b> TG Star\n"
        caption += f"💰 <b>Сумма:</b> {amount} {currency}\n"
        caption += f"📨 <b>Получатель:</b> {username_input}\n\n"
        caption += f"⏰ <b>Время создания:</b> {data['withdraw_requests'][str(withdraw_id)]['timestamp']}\n\n"
        
        await bot.send_message(SUPPORT_GROUP_ID, caption, parse_mode="HTML", reply_markup=withdraw_decision_keyboard(withdraw_id))
    except Exception as e:
        print(f"Ошибка отправки: {e}")
    
    await state.finish()

@dp.callback_query_handler(lambda c: c.data.startswith('withdraw_'), chat_id=SUPPORT_GROUP_ID)
async def process_withdraw_decision(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён! Только для админов.")
        return
    
    action, request_id = callback_query.data.split('_')[1], callback_query.data.split('_')[2]
    data = load_data()
    
    if request_id not in data.get('withdraw_requests', {}):
        await callback_query.answer("❌ Заявка не найдена!")
        return
    
    request_data = data['withdraw_requests'][request_id]
    admin_username = callback_query.from_user.username or callback_query.from_user.first_name
    
    if action == 'accept':
        data['withdraw_requests'][request_id]['status'] = 'completed'
        data['withdraw_requests'][request_id]['admin_action'] = 'accepted'
        data['withdraw_requests'][request_id]['admin_username'] = admin_username
        data['withdraw_requests'][request_id]['action_timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_data(data)
        
        user_id = request_data['user_id']
        if user_id in data['users']:
            game = request_data['game']
            earned_field = f'total_earned_{game}'
            if earned_field not in data['users'][user_id]:
                data['users'][user_id][earned_field] = 0
            data['users'][user_id][earned_field] += request_data['amount']
            save_data(data)
        
        try:
            await bot.send_message(int(request_data['user_id']), f"✅ <b>Заказ выполнен!</b>\n💰 {request_data['amount']} {request_data['currency']}\n✨ <b>Оцените нас:</b>", parse_mode="HTML", reply_markup=rating_keyboard())
            
            user_state = dp.current_state(chat=int(request_data['user_id']), user=int(request_data['user_id']))
            await user_state.update_data(withdraw_id=request_id, amount=request_data['amount'], currency=request_data['currency'], game=request_data['game'])
            await user_state.set_state(UserStates.waiting_review_rating)
        except Exception as e:
            print(f"Ошибка уведомления: {e}")
        
        try:
            if callback_query.message.photo:
                await bot.edit_message_caption(callback_query.message.chat.id, callback_query.message.message_id, caption=f"{callback_query.message.caption}\n\n✅ Принято @{admin_username}", parse_mode="HTML")
            else:
                await bot.edit_message_text(callback_query.message.chat.id, callback_query.message.message_id, text=f"{callback_query.message.text}\n\n✅ Принято @{admin_username}", parse_mode="HTML")
        except:
            pass
        
        await callback_query.answer("✅ Заявка принята")
    
    elif action == 'reject':
        user_id = request_data['user_id']
        if user_id in data['users']:
            if request_data['game'] == 'standoff':
                data['users'][user_id]['balance_standoff'] += request_data['amount']
            elif request_data['game'] == 'roblox':
                data['users'][user_id]['balance_roblox'] += request_data['amount']
            elif request_data['game'] == 'tgstar':
                data['users'][user_id]['balance_tgstar'] += request_data['amount']
        
        data['withdraw_requests'][request_id]['status'] = 'rejected'
        data['withdraw_requests'][request_id]['admin_action'] = 'rejected'
        data['withdraw_requests'][request_id]['admin_username'] = admin_username
        data['withdraw_requests'][request_id]['action_timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_data(data)
        
        try:
            await bot.send_message(int(request_data['user_id']), f"❌ <b>Заявка отклонена.</b>\n💰 Сумма возвращена.", parse_mode="HTML")
        except:
            pass
        
        try:
            if callback_query.message.photo:
                await bot.edit_message_caption(callback_query.message.chat.id, callback_query.message.message_id, caption=f"{callback_query.message.caption}\n\n❌ Отклонено @{admin_username}", parse_mode="HTML")
            else:
                await bot.edit_message_text(callback_query.message.chat.id, callback_query.message.message_id, text=f"{callback_query.message.text}\n\n❌ Отклонено @{admin_username}", parse_mode="HTML")
        except:
            pass
        
        await callback_query.answer("❌ Заявка отклонена")

@dp.callback_query_handler(lambda c: c.data.startswith('rating_'), state=UserStates.waiting_review_rating)
async def process_rating(callback_query: types.CallbackQuery, state: FSMContext):
    rating = int(callback_query.data.split('_')[1])
    await state.update_data(rating=rating)
    
    try:
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    except:
        pass
    
    await bot.send_message(callback_query.message.chat.id, "✍️ <b>Напишите пару слов о нас</b>\n✉️ <b>Скриншот можно приложить далее.</b>", parse_mode="HTML", reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🤫 Промолчать", callback_data="skip_review")))
    await UserStates.waiting_review_text.set()
    await callback_query.answer(f"Оценка: {rating}")

@dp.callback_query_handler(lambda c: c.data == 'skip_review', state=UserStates.waiting_review_text)
async def skip_review_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(review_text="Промолчал...")
    
    try:
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    except:
        pass
    
    await bot.send_message(callback_query.message.chat.id, "📖 <b>Пришлите скриншот товара:</b>", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
    await UserStates.waiting_review_screenshot.set()
    await callback_query.answer()

@dp.message_handler(state=UserStates.waiting_review_text)
async def process_review_text(message: types.Message, state: FSMContext):
    if message.text == "🏠 Главное меню":
        await state.finish()
        data = load_data()
        user_id = str(message.from_user.id)
        user_data = data['users'].get(user_id, {})
        await show_game_menu(message.chat.id, user_data.get('game', 'standoff'), user_data['username'])
        return
    
    await state.update_data(review_text=message.text)
    
    try:
        await message.delete()
    except:
        pass
    
    await message.answer("📖 <b>Пришлите скриншот товара::</b>", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
    await UserStates.waiting_review_screenshot.set()

@dp.message_handler(content_types=['photo'], state=UserStates.waiting_review_screenshot)
async def process_review_screenshot(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    data = load_data()
    
    state_data = await state.get_data()
    rating = state_data.get('rating', 5)
    review_text = state_data.get('review_text', 'Промолчал...')
    withdraw_id = state_data.get('withdraw_id')
    amount = state_data.get('amount')
    currency = state_data.get('currency')
    game = state_data.get('game')
    
    review_id = generate_id(data, 'reviews')
    
    if 'reviews' not in data:
        data['reviews'] = {}
    
    data['reviews'][str(review_id)] = {
        'user_id': user_id,
        'username': message.from_user.username or message.from_user.first_name,
        'rating': rating,
        'text': review_text,
        'withdraw_id': withdraw_id,
        'amount': amount,
        'currency': currency,
        'game': game,
        'status': 'pending',
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'screenshot_file_id': message.photo[-1].file_id
    }
    
    data['stats']['total_reviews'] += 1
    save_data(data)
    
    try:
        await message.delete()
    except:
        pass
    
    await message.answer("✨ <b>Отзыв отправлен на модерацию.</b>", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
    
    try:
        user_number = get_user_number(data, user_id)
        game_names = {'standoff': 'Standoff 2', 'roblox': 'Roblox', 'tgstar': 'TG Star'}
        
        caption = f"📝 <b> Новый отзыв #{review_id}</b>\n\n"
        caption += f"👤 <b>Пользователь:</b> @{message.from_user.username or message.from_user.first_name} ({user_number})\n"
        caption += f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
        caption += f"🎮 <b>Игра:</b> {game_names.get(game, game)}\n\n"
        caption += f"💰 <b>Сумма вывода:</b> {amount} {currency}\n"
        caption += f"⭐️ <b>Оценка:</b> {rating}/5\n"
        caption += f"💬 <b>Текст отзыва:</b> {review_text}\n"
        caption += f"⏰ <b>Время создания:</b> {data['reviews'][str(review_id)]['timestamp']}\n\n"
        
        await bot.send_photo(SUPPORT_GROUP_ID, message.photo[-1].file_id, caption=caption, parse_mode="HTML", reply_markup=review_decision_keyboard(review_id))
    except Exception as e:
        print(f"Ошибка отправки: {e}")
    
    await state.finish()

@dp.callback_query_handler(lambda c: c.data.startswith('review_'), chat_id=SUPPORT_GROUP_ID)
async def process_review_decision(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён! Только для админов.")
        return
    
    action, review_id = callback_query.data.split('_')[1], callback_query.data.split('_')[2]
    data = load_data()
    
    if review_id not in data.get('reviews', {}):
        await callback_query.answer("❌ Отзыв не найден!")
        return
    
    review_data = data['reviews'][review_id]
    
    if action == 'publish':
        data['reviews'][review_id]['status'] = 'published'
        data['reviews'][review_id]['admin_username'] = callback_query.from_user.username or callback_query.from_user.first_name
        data['reviews'][review_id]['publish_timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_data(data)
        
        review_text_display = review_data['text'] if review_data['text'] != "Промолчал..." else "Промолчал..."
        game_names = {'standoff': 'Standoff 2', 'roblox': 'Roblox', 'tgstar': 'TG Star'}
        
        review_message = f"🎁 Отзыв <b>№{review_id}</b>\n\n✉️ Пользователь: {review_data['username']}\n\n✍️ Комментарий: {review_text_display}\n⭐️ Оценка: {review_data['rating']}/5\n\n💰 Товар {review_data['amount']} {review_data['currency']}"
        
        try:
            await bot.send_photo(REVIEWS_CHANNEL_ID, review_data['screenshot_file_id'], caption=review_message, parse_mode="HTML")
        except Exception as e:
            print(f"Ошибка публикации: {e}")
        
        try:
            await bot.edit_message_caption(callback_query.message.chat.id, callback_query.message.message_id, caption=f"{callback_query.message.caption}\n\n✅ Опубликовано @{callback_query.from_user.username or callback_query.from_user.first_name}", parse_mode="HTML")
        except:
            pass
        
        await callback_query.answer("✅ Отзыв опубликован")
    
    elif action == 'reject':
        data['reviews'][review_id]['status'] = 'rejected'
        data['reviews'][review_id]['admin_username'] = callback_query.from_user.username or callback_query.from_user.first_name
        data['reviews'][review_id]['reject_timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_data(data)
        
        try:
            await bot.edit_message_caption(callback_query.message.chat.id, callback_query.message.message_id, caption=f"{callback_query.message.caption}\n\n❌ Отклонено @{callback_query.from_user.username or callback_query.from_user.first_name}", parse_mode="HTML")
        except:
            pass
        
        await callback_query.answer("❌ Отзыв отклонен")

@dp.message_handler(lambda message: message.text in ["💰 Купить голду", "💰 Купить робаксы", "💰 Купить звезды"])
async def process_purchase_button(message: types.Message):
    if message.chat.id == SUPPORT_GROUP_ID:
        return
    
    user_id = str(message.from_user.id)
    data = load_data()
    
    if user_id not in data['users']:
        await message.answer("❌ Пользователь не найден.", parse_mode="HTML")
        return
    
    user_data = data['users'][user_id]
    if user_data.get('banned', False):
        await message.answer("🚫 <b>Вы забанены.</b>", parse_mode="HTML")
        return
    
    current_game = user_data.get('game', 'standoff')
    button_games = {"💰 Купить голду": 'standoff', "💰 Купить робаксы": 'roblox', "💰 Купить звезды": 'tgstar'}
    
    if button_games[message.text] != current_game:
        game_names = {'standoff': 'Standoff 2', 'roblox': 'Roblox', 'tgstar': 'TG Star'}
        await message.answer(f"❌ Функция только для {game_names[button_games[message.text]]}.", parse_mode="HTML")
        return
    
    if has_active_purchase_request(message.from_user.id):
        await message.answer(
            "🕑 <b>Подождите, вашу заявку на пополнение проверяют.</b>\n\nПосле обработки, вы получите уведомление.",
            parse_mode="HTML",
            reply_markup=main_menu_reply_keyboard()
        )
        return
    
    currency_names = {'standoff': 'Gold', 'roblox': 'Robux', 'tgstar': 'Stars'}
    settings = data['settings']
    
    try:
        await message.delete()
    except:
        pass
    
    await message.answer(f"✨ <b>Напиши сумму в UZS для покупки {currency_names[current_game].lower()}:</b>\n📊 <b>Мин.:</b> {settings['min_purchase']:,} UZS\n📈 <b>Макс.:</b> {settings['max_purchase']:,} UZS", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
    await UserStates.waiting_purchase_amount.set()
    await dp.current_state(chat=message.chat.id, user=user_id).update_data(purchase_game=current_game, currency_name=currency_names[current_game])

@dp.message_handler(state=UserStates.waiting_purchase_amount)
async def process_purchase_amount(message: types.Message, state: FSMContext):
    if message.text == "🏠 Главное меню":
        await state.finish()
        data = load_data()
        user_id = str(message.from_user.id)
        user_data = data['users'].get(user_id, {})
        await show_game_menu(message.chat.id, user_data.get('game', 'standoff'), user_data['username'])
        return
    
    try:
        amount_uzs = int(message.text.replace(" ", "").replace(",", ""))
    except:
        await message.answer("❌ Введите число.", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        return
    
    user_id = str(message.from_user.id)
    data = load_data()
    
    if user_id not in data['users']:
        await message.answer("❌ Пользователь не найден.", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        await state.finish()
        return
    
    settings = data['settings']
    
    if amount_uzs < settings['min_purchase']:
        await message.answer(f"❌ Мин. сумма: {settings['min_purchase']:,} UZS", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        return
    if amount_uzs > settings['max_purchase']:
        await message.answer(f"❌ Макс. сумма: {settings['max_purchase']:,} UZS", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        return
    
    state_data = await state.get_data()
    game_type = state_data.get('purchase_game', 'standoff')
    currency_name = state_data.get('currency_name', 'Gold')
    
    rate = settings['exchange_rates'].get(game_type, 125)
    amount_currency = amount_uzs // rate
    
    if amount_currency <= 0:
        await message.answer("❌ Сумма слишком мала.", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        return
    
    await state.update_data(amount_uzs=amount_uzs, amount_currency=amount_currency, exchange_rate=rate)
    
    try:
        await message.delete()
    except:
        pass
    
    await message.answer(f"💡 <b>За {amount_uzs:,} UZS вы получите {amount_currency:,} {currency_name}</b>\n💰 <b>Курс:</b> 1 {currency_name} = {rate:,} UZS", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
    
    payment_data = load_payment_methods()
    available_methods = []
    
    for method in payment_data['methods']:
        if method['game'] == game_type or method['game'] == 'all':
            available_methods.append(method)
    
    if not available_methods:
        await message.answer("❌ Нет способов оплаты.", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        await state.finish()
        return
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    for method in available_methods:
        btn_text = f"🏦 {method['bank_name']}"
        if method.get('card'):
            btn_text += f" • {method['card'][-4:]}"
        callback_data = f"pay_method_{method['id']}"
        keyboard.add(InlineKeyboardButton(btn_text, callback_data=callback_data))
    
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="purchase_back"))
    
    await message.answer("👇 <b>Выберите способ оплаты:</b>", parse_mode="HTML", reply_markup=keyboard)
    await UserStates.waiting_payment_method_choice.set()

@dp.callback_query_handler(lambda c: c.data.startswith('pay_method_'), state=UserStates.waiting_payment_method_choice)
async def process_payment_method_choice(callback_query: types.CallbackQuery, state: FSMContext):
    method_id = int(callback_query.data.split('_')[2])
    
    payment_data = load_payment_methods()
    selected_method = None
    
    for method in payment_data['methods']:
        if method['id'] == method_id:
            selected_method = method
            break
    
    if not selected_method:
        await callback_query.answer("❌ Способ не найден")
        return
    
    state_data = await state.get_data()
    currency_name = state_data.get('currency_name', 'Gold')
    amount_uzs = state_data.get('amount_uzs')
    amount_currency = state_data.get('amount_currency')
    
    try:
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    except:
        pass
    
    payment_info = f"✉️ <b>Банк:</b> {selected_method['bank_name']}\n👤 <b>Получатель:</b> {selected_method['recipient_name']}\n"
    if selected_method.get('card'):
        payment_info += f"💳 <b>Карта:</b> {selected_method['card']}\n"
    if selected_method.get('phone'):
        payment_info += f"📱 <b>Телефон:</b> {selected_method['phone']}\n"
    payment_info += f"\n💰 <b>Сумма:</b> {amount_uzs:,} UZS\n🍯 <b>Получите:</b> {amount_currency:,} {currency_name}\n\n✅ <b>После оплаты отправьте скриншот</b>"
    
    await bot.send_message(callback_query.message.chat.id, payment_info, parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
    
    await state.update_data(
        payment_method_id=method_id,
        payment_method_bank=selected_method['bank_name'],
        payment_method_recipient=selected_method['recipient_name']
    )
    
    await UserStates.waiting_purchase_screenshot.set()
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == 'purchase_back', state=UserStates.waiting_payment_method_choice)
async def purchase_back_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    
    try:
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    except:
        pass
    
    data = load_data()
    user_id = str(callback_query.from_user.id)
    user_data = data['users'].get(user_id, {})
    await show_game_menu(callback_query.message.chat.id, user_data.get('game', 'standoff'), user_data['username'])
    await callback_query.answer()

@dp.message_handler(content_types=['photo'], state=UserStates.waiting_purchase_screenshot)
async def process_purchase_screenshot(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    data = load_data()
    
    if user_id not in data['users']:
        await message.answer("❌ Пользователь не найден.", parse_mode="HTML")
        await state.finish()
        return
    
    state_data = await state.get_data()
    amount_uzs = state_data.get('amount_uzs')
    amount_currency = state_data.get('amount_currency')
    game_type = state_data.get('purchase_game', 'standoff')
    currency_name = state_data.get('currency_name', 'Gold')
    payment_method_bank = state_data.get('payment_method_bank', '')
    
    if not amount_uzs or not amount_currency:
        await message.answer("❌ Ошибка данных.", parse_mode="HTML")
        await state.finish()
        return
    
    purchase_id = generate_id(data, 'purchase_requests')
    
    if 'purchase_requests' not in data:
        data['purchase_requests'] = {}
    
    data['purchase_requests'][str(purchase_id)] = {
        'user_id': user_id,
        'username': message.from_user.username or message.from_user.first_name,
        'amount_uzs': amount_uzs,
        'amount_currency': amount_currency,
        'game': game_type,
        'currency_name': currency_name,
        'payment_method_bank': payment_method_bank,
        'status': 'pending',
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'screenshot_file_id': message.photo[-1].file_id
    }
    
    save_data(data)
    
    try:
        await message.delete()
    except:
        pass
    
    await message.answer("✉️ <b>Заявка отправлена на проверку.</b>", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
    
    try:
        user_number = get_user_number(data, user_id)
        game_names = {'standoff': 'Standoff 2', 'roblox': 'Roblox', 'tgstar': 'TG Star'}
        
        caption = f"🛒 <b>Заявка на покупку #{purchase_id}</b> <code>({user_number})</code>\n\n"
        caption += f"👤 <b>Пользователь:</b> @{message.from_user.username or message.from_user.first_name}\n"
        caption += f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
        caption += f"🎮 <b>Игра:</b> {game_names[game_type]}\n\n"
        caption += f"💰 <b>Сумма оплаты:</b> {amount_uzs:,} UZS\n"
        caption += f"🍯 <b>Получит:</b> {amount_currency:,} {currency_name}\n\n"
        caption += f"⏰ <b>Время создания:</b> {data['purchase_requests'][str(purchase_id)]['timestamp']}\n\n"
        
        await bot.send_photo(SUPPORT_GROUP_ID, message.photo[-1].file_id, caption=caption, parse_mode="HTML", reply_markup=purchase_decision_keyboard(purchase_id))
    except Exception as e:
        print(f"Ошибка отправки: {e}")
    
    await state.finish()

@dp.callback_query_handler(lambda c: c.data.startswith('purchase_'), chat_id=SUPPORT_GROUP_ID)
async def process_purchase_decision(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён! Только для админов.")
        return
    
    action, purchase_id = callback_query.data.split('_')[1], callback_query.data.split('_')[2]
    data = load_data()
    
    if purchase_id not in data.get('purchase_requests', {}):
        await callback_query.answer("❌ Заявка не найдена!")
        return
    
    purchase_data = data['purchase_requests'][purchase_id]
    admin_username = callback_query.from_user.username or callback_query.from_user.first_name
    
    if action == 'accept':
        data['purchase_requests'][purchase_id]['status'] = 'completed'
        data['purchase_requests'][purchase_id]['admin_action'] = 'accepted'
        data['purchase_requests'][purchase_id]['admin_username'] = admin_username
        data['purchase_requests'][purchase_id]['action_timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        user_id = purchase_data['user_id']
        if user_id in data['users']:
            game_type = purchase_data['game']
            amount_currency = purchase_data['amount_currency']
            
            if game_type == 'standoff':
                data['users'][user_id]['balance_standoff'] += amount_currency
            elif game_type == 'roblox':
                data['users'][user_id]['balance_roblox'] += amount_currency
            elif game_type == 'tgstar':
                data['users'][user_id]['balance_tgstar'] += amount_currency
            
            referrer_id = data['users'][user_id].get('referrer_id')
            if referrer_id and referrer_id in data['users'] and referrer_id != user_id:
                percent = data['referral_settings'].get(f'{game_type}_percent', 10)
                bonus_amount = int(amount_currency * percent / 100)
                
                if bonus_amount > 0:
                    if game_type == 'standoff':
                        data['users'][referrer_id]['balance_standoff'] += bonus_amount
                        data['users'][referrer_id]['total_ref_earned_standoff'] += bonus_amount
                    elif game_type == 'roblox':
                        data['users'][referrer_id]['balance_roblox'] += bonus_amount
                        data['users'][referrer_id]['total_ref_earned_roblox'] += bonus_amount
                    elif game_type == 'tgstar':
                        data['users'][referrer_id]['balance_tgstar'] += bonus_amount
                        data['users'][referrer_id]['total_ref_earned_tgstar'] += bonus_amount
                    
                    try:
                        referrer_bonus_text = f"🎉 <b>Вам начислен реферальный бонус!</b>\n👤 Реферал: @{purchase_data['username']}\n💰 Сумма покупки: {amount_currency:,} {purchase_data['currency_name']}\n🎁 Ваш бонус: {bonus_amount:,} {purchase_data['currency_name']}\n📊 Процент: {percent}%"
                        await bot.send_message(int(referrer_id), referrer_bonus_text, parse_mode="HTML")
                    except Exception as e:
                        print(f"Ошибка уведомления реферера: {e}")
        
        data['stats']['total_purchases'] += 1
        data['stats']['total_purchases_amount'] += purchase_data['amount_uzs']
        save_data(data)
        
        try:
            await bot.send_message(int(purchase_data['user_id']), f"✅ <b>Покупка подтверждена!</b>\n💰 {purchase_data['amount_currency']:,} {purchase_data['currency_name']}\n💵 {purchase_data['amount_uzs']:,} UZS", parse_mode="HTML")
        except Exception as e:
            print(f"Ошибка уведомления: {e}")
        
        try:
            await bot.edit_message_caption(callback_query.message.chat.id, callback_query.message.message_id, caption=f"{callback_query.message.caption}\n\n✅ Принято @{admin_username}", parse_mode="HTML")
        except:
            pass
        
        await callback_query.answer("✅ Заявка принята")
    
    elif action == 'reject':
        data['purchase_requests'][purchase_id]['status'] = 'rejected'
        data['purchase_requests'][purchase_id]['admin_action'] = 'rejected'
        data['purchase_requests'][purchase_id]['admin_username'] = admin_username
        data['purchase_requests'][purchase_id]['action_timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_data(data)
        
        try:
            await bot.send_message(int(purchase_data['user_id']), f"❌ <b>Заявка отклонена.</b>\n⚠️ <b>Обратитесь в поддержку.</b>", parse_mode="HTML")
        except:
            pass
        
        try:
            await bot.edit_message_caption(callback_query.message.chat.id, callback_query.message.message_id, caption=f"{callback_query.message.caption}\n\n❌ Отклонено @{admin_username}", parse_mode="HTML")
        except:
            pass
        
        await callback_query.answer("❌ Заявка отклонена")

@dp.message_handler(lambda message: message.text == "🔢 Посчитать")
async def calculator_button(message: types.Message):
    if message.chat.id == SUPPORT_GROUP_ID:
        return
    
    user_id = str(message.from_user.id)
    data = load_data()
    
    if user_id not in data['users']:
        await message.answer("❌ Пользователь не найден.", parse_mode="HTML")
        return
    
    user_data = data['users'][user_id]
    current_game = user_data.get('game', 'standoff')
    currency_names = {'standoff': 'Gold', 'roblox': 'Robux', 'tgstar': 'Stars'}
    currency = currency_names[current_game]
    rate = data['settings']['exchange_rates'].get(current_game, 125)
    
    try:
        await message.delete()
    except:
        pass
    
    await message.answer(f"👇 <b>Выберите тип расчета:</b>", parse_mode="HTML", reply_markup=calculator_type_keyboard())
    await dp.current_state(chat=message.chat.id, user=user_id).update_data(calc_game=current_game, calc_currency=currency, calc_rate=rate)

@dp.callback_query_handler(lambda c: c.data in ['calc_to_game', 'calc_to_uzs', 'calc_back'])
async def calculator_type_callback(callback_query: types.CallbackQuery):
    if callback_query.data == 'calc_back':
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
        data = load_data()
        user_id = str(callback_query.from_user.id)
        user_data = data['users'].get(user_id, {})
        await show_game_menu(callback_query.message.chat.id, user_data.get('game', 'standoff'), user_data['username'])
        await callback_query.answer()
        return
    
    state = dp.current_state(chat=callback_query.message.chat.id, user=callback_query.from_user.id)
    await state.set_state(UserStates.waiting_calculator_value)
    
    if callback_query.data == 'calc_to_game':
        await state.update_data(calc_type='to_game')
        await bot.edit_message_text(
            "💰 <b>Введите сумму в UZS</b>",
            callback_query.message.chat.id, callback_query.message.message_id,
            parse_mode="HTML"
        )
    else:
        await state.update_data(calc_type='to_uzs')
        await bot.edit_message_text(
            "🎮 <b>Введите сумму в валюте</b>",
            callback_query.message.chat.id, callback_query.message.message_id,
            parse_mode="HTML"
        )
    
    await callback_query.answer()

@dp.message_handler(state=UserStates.waiting_calculator_value)
async def process_calculator_value(message: types.Message, state: FSMContext):
    if message.text == "🏠 Главное меню":
        await state.finish()
        data = load_data()
        user_id = str(message.from_user.id)
        user_data = data['users'].get(user_id, {})
        await show_game_menu(message.chat.id, user_data.get('game', 'standoff'), user_data['username'])
        return
    
    try:
        value = int(message.text.replace(" ", "").replace(",", ""))
    except:
        await message.answer("❌ Введите число.", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        return
    
    state_data = await state.get_data()
    calc_type = state_data.get('calc_type')
    game = state_data.get('calc_game', 'standoff')
    currency = state_data.get('calc_currency', 'Gold')
    rate = state_data.get('calc_rate', 125)
    
    if calc_type == 'to_game':
        result = value // rate
        await message.answer(f"💵 {value:,} UZS = {result:,} {currency}", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
    else:
        result = value * rate
        await message.answer(f"🎮 {value:,} {currency} = {result:,} UZS", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
    
    await state.finish()

@dp.message_handler(lambda message: message.text == "📖 Поддержка")
async def support_button(message: types.Message):
    if message.chat.id == SUPPORT_GROUP_ID:
        return
    
    user_id = str(message.from_user.id)
    data = load_data()
    
    if user_id not in data['users']:
        await message.answer("❌ Пользователь не найден.", parse_mode="HTML")
        return
    
    try:
        await message.delete()
    except:
        pass
    
    await message.answer("✏️ <b>Напишите ваш вопрос:</b>", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
    await SupportStates.waiting_for_question.set()

@dp.message_handler(state=SupportStates.waiting_for_question)
async def process_support_question(message: types.Message, state: FSMContext):
    if message.text == "🏠 Главное меню":
        await state.finish()
        data = load_data()
        user_id = str(message.from_user.id)
        user_data = data['users'].get(user_id, {})
        await show_game_menu(message.chat.id, user_data.get('game', 'standoff'), user_data['username'])
        return
    
    user_id = str(message.from_user.id)
    data = load_data()
    
    ticket_id = generate_id(data, 'support_tickets')
    
    ticket_data = {
        'user_id': user_id,
        'username': message.from_user.username or message.from_user.first_name,
        'message': message.text,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'status': 'pending'
    }
    
    if 'support_tickets' not in data:
        data['support_tickets'] = {}
    data['support_tickets'][str(ticket_id)] = ticket_data
    save_data(data)
    
    try:
        await message.delete()
    except:
        pass
    
    await message.answer("✅ <b>Ваш вопрос отправлен в поддержку.</b>\n⏰ <i>Ожидайте ответа в ближайшее время.</i>", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
    
    reply_keyboard = InlineKeyboardMarkup(row_width=1)
    reply_keyboard.add(
        InlineKeyboardButton(text="✏️ Ответить", callback_data=f"reply_{ticket_id}"),
        InlineKeyboardButton(text="✅ Решено", callback_data=f"resolve_{ticket_id}")
    )
    
    try:
        user_number = get_user_number(data, user_id)
        notification = (
            f"❓ <b>Новый вопрос #{ticket_id}</b>\n"
            f"👤 @{message.from_user.username or message.from_user.first_name}\n"
            f"🔢 Номер: {user_number}\n"
            f"🆔 ID: <code>{user_id}</code>\n"
            f"⏰ Время создания: {ticket_data['timestamp']}\n\n"
            f"📝 <b>Вопрос:</b>\n{message.text}\n\n")
        
        await bot.send_message(SUPPORT_GROUP_ID, notification, parse_mode="HTML", reply_markup=reply_keyboard)
    except Exception as e:
        print(f"Ошибка отправки в группу: {e}")
    
    await state.finish()

@dp.callback_query_handler(lambda c: c.data.startswith('reply_'), chat_id=SUPPORT_GROUP_ID)
async def reply_to_ticket_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён! Только для админов.")
        return
    
    ticket_id = callback_query.data.split('_')[1]
    data = load_data()
    
    if ticket_id not in data.get('support_tickets', {}):
        await callback_query.answer("❌ Вопрос не найден!")
        await bot.edit_message_reply_markup(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            reply_markup=None
        )
        return
    
    ticket_data = data['support_tickets'][ticket_id]
    
    admin_username = callback_query.from_user.username or callback_query.from_user.first_name
    await callback_query.answer(f"Вы взяли вопрос #{ticket_id}")
    
    ticket_data['status'] = 'in_progress'
    ticket_data['admin_username'] = admin_username
    save_data(data)
    
    await bot.send_message(
        callback_query.message.chat.id,
        f"✏️ <b>Введите ответ для пользователя:</b>\n<i>Или отправьте 'отмена' для отмены</i>",
        parse_mode="HTML"
    )
    
    await AdminStates.waiting_admin_reply.set()
    await dp.current_state(user=callback_query.from_user.id).update_data(ticket_id=ticket_id, user_id=ticket_data.get('user_id'), original_message_id=callback_query.message.message_id)

@dp.callback_query_handler(lambda c: c.data.startswith('resolve_'), chat_id=SUPPORT_GROUP_ID)
async def resolve_ticket_callback(callback_query: types.CallbackQuery):
    ticket_id = callback_query.data.split('_')[1]
    data = load_data()
    
    if ticket_id not in data.get('support_tickets', {}):
        await callback_query.answer("❌ Вопрос не найден!")
        return
    
    ticket_data = data['support_tickets'][ticket_id]
    admin_username = callback_query.from_user.username or callback_query.from_user.first_name
    
    ticket_data['status'] = 'resolved'
    ticket_data['resolved_by'] = admin_username
    ticket_data['resolved_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_data(data)
    
    await callback_query.answer(f"✅ Вопрос #{ticket_id} отмечен как решенный")
    
    try:
        await bot.edit_message_text(
            f"✅ <b>Вопрос #{ticket_id} решен</b>\n👤 Пользователь: @{ticket_data.get('username', 'N/A')}\n👨‍💼 Решил: @{admin_username}\n📝 <b>Вопрос был:</b>\n{ticket_data.get('message', '')}",
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Ошибка обновления сообщения: {e}")

@dp.message_handler(state=AdminStates.waiting_admin_reply)
async def process_admin_reply(message: types.Message, state: FSMContext):
    if message.text.lower() == 'отмена':
        await state.finish()
        await message.answer("❌ Ответ отменен.", parse_mode="HTML")
        return
    
    state_data = await state.get_data()
    ticket_id = state_data.get('ticket_id')
    user_id = state_data.get('user_id')
    original_message_id = state_data.get('original_message_id')
    
    data = load_data()
    
    if ticket_id in data.get('support_tickets', {}):
        ticket_data = data['support_tickets'][ticket_id]
        ticket_data['status'] = 'answered'
        ticket_data['admin_reply'] = message.text
        ticket_data['admin_username'] = message.from_user.username or message.from_user.first_name
        ticket_data['reply_timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_data(data)
    
    try:
        await bot.send_message(int(user_id), f"📨 <b>Ответ от поддержки:</b>\n\n{message.text}\n\n<i>Если вопрос решен, можете продолжить пользоваться ботом.</i>", parse_mode="HTML")
        
        if original_message_id:
            await bot.edit_message_text(
                f"✅ <b>Вопрос #{ticket_id} отвечен</b>\n👤 Пользователь: @{ticket_data.get('username', 'N/A')}\n👨‍💼 Ответил: @{message.from_user.username or message.from_user.first_name}\n📝 <b>Вопрос был:</b>\n{ticket_data.get('message', '')}\n\n💬 <b>Ответ:</b>\n{message.text}",
                chat_id=SUPPORT_GROUP_ID,
                message_id=original_message_id,
                parse_mode="HTML"
            )
        
        await message.answer(f"✅ <b>Ответ отправлен пользователю {user_id}</b>", parse_mode="HTML")
    except Exception as e:
        print(f"Ошибка отправки ответа: {e}")
        await message.answer(f"❌ <b>Не удалось отправить ответ пользователю {user_id}</b>\nОшибка: {str(e)}", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
    
    await state.finish()

@dp.message_handler(commands=['adm'])
async def cmd_admpanel(message: types.Message):
    if message.chat.id == SUPPORT_GROUP_ID:
        return
    
    if message.from_user.id in ADMIN_IDS:
        try:
            await message.delete()
        except:
            pass
        await message.answer("⚡️ <b> Админ панель успешно активирована</b>", parse_mode="HTML", reply_markup=admin_keyboard())

@dp.message_handler(commands=['work'], chat_id=SUPPORT_GROUP_ID)
async def cmd_work(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        try:
            await message.delete()
        except:
            pass
        return
    
    data = load_data()
    
    purchase_requests = data.get('purchase_requests', {})
    pending_purchases = sum(1 for r in purchase_requests.values() if r.get('status') == 'pending')
    
    withdraw_requests = data.get('withdraw_requests', {})
    pending_withdraws = sum(1 for r in withdraw_requests.values() if r.get('status') == 'pending')
    
    support_tickets = data.get('support_tickets', {})
    unanswered_questions = sum(1 for t in support_tickets.values() if t.get('status') in ['pending', 'in_progress'])
    
    reviews = data.get('reviews', {})
    pending_reviews = sum(1 for r in reviews.values() if r.get('status') == 'pending')
    
    text = f"🔥 <b>Вы включились в режим работы!</b>\n\n"
    text += f"✨ <b>Вам нужно проверить:</b>\n"
    text += f"• {pending_purchases} заявок на пополнение.\n"
    text += f"• {pending_withdraws} заявок на вывод.\n"
    text += f"• {unanswered_questions} вопросов.\n"
    text += f"• {pending_reviews} отзывов.\n\n"
    text += f"<i>Используйте кнопки ниже для работы</i>"
    
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(KeyboardButton("🛍 Заявки"), KeyboardButton("📊 Статистика"))
    keyboard.add(KeyboardButton("👑 Админ панель"))
    
    try:
        await message.delete()
    except:
        pass
    
    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)

@dp.message_handler(lambda message: message.text == "🛍 Заявки", chat_id=SUPPORT_GROUP_ID)
async def group_requests_button(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🍯 Выводы", callback_data="group_requests_withdraw"),
        InlineKeyboardButton("💰 Пополнения", callback_data="group_requests_purchase")
    )
    keyboard.add(
        InlineKeyboardButton("💥 Отзывы", callback_data="group_requests_reviews"),
        InlineKeyboardButton("❓ Вопросы", callback_data="group_requests_questions")
    )
    keyboard.add(InlineKeyboardButton("🔍 Найти заявку", callback_data="group_requests_search"))
    
    try:
        await message.delete()
    except:
        pass
    
    await message.answer("💎 <b>Выберите тип заявки:</b>", parse_mode="HTML", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == 'group_requests_withdraw')
async def group_requests_withdraw_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        InlineKeyboardButton("🎮 Standoff2", callback_data="group_withdraw_standoff"),
        InlineKeyboardButton("🔲 Roblox", callback_data="group_withdraw_roblox"),
        InlineKeyboardButton("⭐️ Tg star", callback_data="group_withdraw_tgstar")
    )
    keyboard.add(InlineKeyboardButton("⬅️ Назад", callback_data="group_back_to_requests"))
    
    await bot.edit_message_text(
        "🤩 <b>Выберите игру для проверки выводов:</b>",
        callback_query.message.chat.id,
        callback_query.message.message_id,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('group_withdraw_'))
async def group_withdraw_game_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    game = callback_query.data.split('_')[2]
    data = load_data()
    withdraw_requests = data.get('withdraw_requests', {})
    
    pending_requests = {}
    for req_id, req_data in withdraw_requests.items():
        if req_data.get('game') == game and req_data.get('status') == 'pending':
            pending_requests[req_id] = req_data
    
    if not pending_requests:
        await callback_query.answer("📭 Нет непроверенных заявок на вывод!")
        return
    
    game_names = {'standoff': 'Standoff 2', 'roblox': 'Roblox', 'tgstar': 'TG Star'}
    currency = {'standoff': 'Gold', 'roblox': 'Robux', 'tgstar': 'Stars'}[game]
    
    text = f"🍯 <b>Выберите заявку на вывод:</b>\n"
    text += f"🎮 <b>Игра:</b> {game_names[game]}\n"
    text += f"📊 <b>Непроверенных заявок:</b> {len(pending_requests)}\n\n"
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    for req_id, req_data in list(pending_requests.items())[:15]:
        amount = req_data.get('amount', 0)
        if game == 'standoff':
            btn_text = f"💥 #{req_id} | {amount}G"
        elif game == 'roblox':
            btn_text = f"💥 #{req_id} | {amount} RBX"
        else:
            btn_text = f"💥 #{req_id} | {amount} ⭐"
        
        keyboard.add(InlineKeyboardButton(btn_text, callback_data=f"group_view_withdraw_{req_id}"))
    
    keyboard.add(InlineKeyboardButton("⬅️ Назад", callback_data="group_requests_withdraw"))
    
    await bot.edit_message_text(
        text,
        callback_query.message.chat.id,
        callback_query.message.message_id,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('group_view_withdraw_'))
async def group_view_withdraw_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    request_id = callback_query.data.split('_')[3]
    data = load_data()
    
    if request_id not in data.get('withdraw_requests', {}):
        await callback_query.answer("❌ Заявка не найдена!")
        return
    
    request_data = data['withdraw_requests'][request_id]
    user_id = request_data.get('user_id')
    user_number = get_user_number(data, user_id) if user_id in data['users'] else "N/A"
    
    game = request_data.get('game', 'standoff')
    game_names = {'standoff': 'Standoff 2', 'roblox': 'Roblox', 'tgstar': 'TG Star'}
    currency = {'standoff': 'Gold', 'roblox': 'Robux', 'tgstar': 'Stars'}[game]
    
    caption = f"📋 <b>Заявка на вывод #{request_id}</b> <code>({user_number})</code>\n\n"
    caption += f"👤 <b>Пользователь:</b> @{request_data.get('username', 'N/A')}\n"
    caption += f"🆔 <b>ID:</b> <code>{user_id}</code>\n\n"
    caption += f"🎮 <b>Игра:</b> {game_names[game]}\n"
    caption += f"💰 <b>Сумма:</b> {request_data.get('amount', 0)} {currency}\n"
    
    if game == 'standoff':
        caption += f"🏷️ <b>Цена на рынке:</b> {request_data.get('market_price', 0)} G\n"
    
    if game == 'roblox':
        caption += f"🎮 <b>Способ:</b> {request_data.get('method', 'N/A')}\n"
        if request_data.get('gamepass_id'):
            caption += f"🆔 <b>GamePass ID:</b> <code>{request_data.get('gamepass_id')}</code>\n"
    
    if game == 'tgstar' and request_data.get('receiver_username'):
        caption += f"📨 <b>Получатель:</b> {request_data.get('receiver_username')}\n"
    
    caption += f"⏰ <b>Время создания:</b> {request_data.get('timestamp', 'N/A')}\n"
    caption += f"📊 <b>Статус:</b> {'⏳ Ожидает' if request_data.get('status') == 'pending' else '✅ Принята' if request_data.get('status') == 'completed' else '❌ Отклонена'}\n\n"
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    if request_data.get('status') == 'pending':
        keyboard.add(
            InlineKeyboardButton("✅ Принять", callback_data=f"withdraw_accept_{request_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"withdraw_reject_{request_id}")
        )
    
    keyboard.add(InlineKeyboardButton("⬅️ Назад", callback_data=f"group_withdraw_{game}"))
    
    if request_data.get('screenshot_file_id') and game == 'standoff':
        try:
            await bot.send_photo(
                callback_query.message.chat.id,
                request_data['screenshot_file_id'],
                caption=caption,
                parse_mode="HTML",
                reply_markup=keyboard
            )
            await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
        except:
            await bot.send_message(
                callback_query.message.chat.id,
                f"{caption}\n\n❌ <i>Не удалось загрузить скриншот</i>",
                parse_mode="HTML",
                reply_markup=keyboard
            )
    else:
        await bot.edit_message_text(
            caption,
            callback_query.message.chat.id,
            callback_query.message.message_id,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == 'group_requests_purchase')
async def group_requests_purchase_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    data = load_data()
    purchase_requests = data.get('purchase_requests', {})
    
    pending_requests = {}
    for req_id, req_data in purchase_requests.items():
        if req_data.get('status') == 'pending':
            pending_requests[req_id] = req_data
    
    if not pending_requests:
        await callback_query.answer("📭 Нет непроверенных заявок на пополнение!")
        return
    
    text = f"💰 <b>Заявки на пополнение</b>\n"
    text += f"📊 <b>Непроверенных заявок:</b> {len(pending_requests)}\n\n"
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    for req_id, req_data in list(pending_requests.items())[:15]:
        game = req_data.get('game', 'standoff')
        game_names = {'standoff': 'Standoff 2', 'roblox': 'Roblox', 'tgstar': 'TG Star'}
        currency = {'standoff': 'Gold', 'roblox': 'Robux', 'tgstar': 'Stars'}[game]
        
        amount_currency = req_data.get('amount_currency', 0)
        amount_uzs = req_data.get('amount_uzs', 0)
        
        btn_text = f"🛒 #{req_id} | {amount_currency} {currency} | {amount_uzs:,} UZS"
        keyboard.add(InlineKeyboardButton(btn_text, callback_data=f"group_view_purchase_{req_id}"))
    
    keyboard.add(InlineKeyboardButton("⬅️ Назад", callback_data="group_back_to_requests"))
    
    await bot.send_message(
        callback_query.message.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    
    try:
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    except:
        pass
    
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('group_view_purchase_'))
async def group_view_purchase_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    request_id = callback_query.data.split('_')[3]
    data = load_data()
    
    if request_id not in data.get('purchase_requests', {}):
        await callback_query.answer("❌ Заявка не найдена!")
        return
    
    request_data = data['purchase_requests'][request_id]
    user_id = request_data.get('user_id')
    user_number = get_user_number(data, user_id) if user_id in data['users'] else "N/A"
    
    game = request_data.get('game', 'standoff')
    game_names = {'standoff': 'Standoff 2', 'roblox': 'Roblox', 'tgstar': 'TG Star'}
    currency = request_data.get('currency_name', 'Gold')
    
    caption = f"🛒 <b>Заявка на покупку #{request_id}</b> <code>({user_number})</code>\n\n"
    caption += f"👤 <b>Пользователь:</b> @{request_data.get('username', 'N/A')}\n"
    caption += f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
    caption += f"🎮 <b>Игра:</b> {game_names[game]}\n\n"
    caption += f"💰 <b>Сумма оплаты:</b> {request_data.get('amount_uzs', 0):,} UZS\n"
    caption += f"🍯 <b>Получит:</b> {request_data.get('amount_currency', 0):,} {currency}\n"
    caption += f"🏦 <b>Способ оплаты:</b> {request_data.get('payment_method_bank', 'N/A')}\n\n"
    caption += f"⏰ <b>Время создания:</b> {request_data.get('timestamp', 'N/A')}\n"
    caption += f"📊 <b>Статус:</b> {'⏳ Ожидает' if request_data.get('status') == 'pending' else '✅ Принята' if request_data.get('status') == 'completed' else '❌ Отклонена'}\n\n"
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    if request_data.get('status') == 'pending':
        keyboard.add(
            InlineKeyboardButton("✅ Принять", callback_data=f"purchase_accept_{request_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"purchase_reject_{request_id}")
        )
    
    keyboard.add(InlineKeyboardButton("⬅️ Назад к списку", callback_data="group_requests_purchase"))
    
    if request_data.get('screenshot_file_id'):
        try:
            await bot.send_photo(
                callback_query.message.chat.id,
                request_data['screenshot_file_id'],
                caption=caption,
                parse_mode="HTML",
                reply_markup=keyboard
            )
        except:
            await bot.send_message(
                callback_query.message.chat.id,
                f"{caption}\n\n❌ <i>Не удалось загрузить скриншот чека</i>",
                parse_mode="HTML",
                reply_markup=keyboard
            )
    else:
        await bot.send_message(
            callback_query.message.chat.id,
            caption,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == 'group_requests_reviews')
async def group_requests_reviews_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    data = load_data()
    reviews = data.get('reviews', {})
    
    pending_reviews = {}
    for rev_id, rev_data in reviews.items():
        if rev_data.get('status') == 'pending':
            pending_reviews[rev_id] = rev_data
    
    if not pending_reviews:
        await callback_query.answer("📭 Нет отзывов на модерации!")
        return
    
    text = f"💥 <b>Отзывы на модерации</b>\n"
    text += f"📊 <b>Отзывов на проверке:</b> {len(pending_reviews)}\n\n"
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    for rev_id, rev_data in list(pending_reviews.items())[:15]:
        game = rev_data.get('game', 'standoff')
        game_names = {'standoff': 'Standoff 2', 'roblox': 'Roblox', 'tgstar': 'TG Star'}
        rating = rev_data.get('rating', 5)
        
        btn_text = f"⭐ #{rev_id} | {rating}/5 | {game_names.get(game, game)}"
        keyboard.add(InlineKeyboardButton(btn_text, callback_data=f"group_view_review_{rev_id}"))
    
    keyboard.add(InlineKeyboardButton("⬅️ Назад", callback_data="group_back_to_requests"))
    
    await bot.send_message(
        callback_query.message.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    
    try:
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    except:
        pass
    
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('group_view_review_'))
async def group_view_review_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    review_id = callback_query.data.split('_')[3]
    data = load_data()
    
    if review_id not in data.get('reviews', {}):
        await callback_query.answer("❌ Отзыв не найден!")
        return
    
    review_data = data['reviews'][review_id]
    user_id = review_data.get('user_id')
    user_number = get_user_number(data, user_id) if user_id in data['users'] else "N/A"
    
    game = review_data.get('game', 'standoff')
    game_names = {'standoff': 'Standoff 2', 'roblox': 'Roblox', 'tgstar': 'TG Star'}
    
    caption = f"📝 <b>Отзыв #{review_id}</b> <code>({user_number})</code>\n\n"
    caption += f"👤 <b>Пользователь:</b> @{review_data.get('username', 'N/A')}\n"
    caption += f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
    caption += f"🎮 <b>Игра:</b> {game_names[game]}\n\n"
    caption += f"⭐️ <b>Оценка:</b> {review_data.get('rating', 5)}/5\n"
    caption += f"💬 <b>Текст:</b> {review_data.get('text', 'N/A')}\n\n"
    caption += f"⏰ <b>Время создания:</b> {review_data.get('timestamp', 'N/A')}\n"
    caption += f"📊 <b>Статус:</b> {'⏳ Ожидает' if review_data.get('status') == 'pending' else '✅ Опубликован' if review_data.get('status') == 'published' else '❌ Отклонен'}\n\n"
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    if review_data.get('status') == 'pending':
        keyboard.add(
            InlineKeyboardButton("✅ Выложить", callback_data=f"review_publish_{review_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"review_reject_{review_id}")
        )
    
    keyboard.add(InlineKeyboardButton("⬅️ Назад к списку", callback_data="group_requests_reviews"))
    
    if review_data.get('screenshot_file_id'):
        try:
            await bot.send_photo(
                callback_query.message.chat.id,
                review_data['screenshot_file_id'],
                caption=caption,
                parse_mode="HTML",
                reply_markup=keyboard
            )
        except:
            await bot.send_message(
                callback_query.message.chat.id,
                f"{caption}\n\n❌ <i>Не удалось загрузить скриншот</i>",
                parse_mode="HTML",
                reply_markup=keyboard
            )
    else:
        await bot.send_message(
            callback_query.message.chat.id,
            caption,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == 'group_requests_questions')
async def group_requests_questions_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    data = load_data()
    support_tickets = data.get('support_tickets', {})
    
    unanswered_questions = {}
    for ticket_id, ticket_data in support_tickets.items():
        if ticket_data.get('status') in ['pending', 'in_progress']:
            unanswered_questions[ticket_id] = ticket_data
    
    if not unanswered_questions:
        await callback_query.answer("📭 Нет неотвеченных вопросов!")
        return
    
    text = f"❓ <b>Неотвеченные вопросы</b>\n"
    text += f"📊 <b>Вопросов на ответ:</b> {len(unanswered_questions)}\n\n"
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    for ticket_id, ticket_data in list(unanswered_questions.items())[:10]:
        username = ticket_data.get('username', 'N/A')
        btn_text = f"📝 #{ticket_id} | @{username}"
        keyboard.add(InlineKeyboardButton(btn_text, callback_data=f"group_reply_{ticket_id}"))
    
    keyboard.add(InlineKeyboardButton("⬅️ Назад", callback_data="group_back_to_requests"))
    
    await bot.send_message(
        callback_query.message.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    
    try:
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    except:
        pass
    
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('group_reply_'))
async def group_reply_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    ticket_id = callback_query.data.split('_')[2]
    data = load_data()
    
    if ticket_id not in data.get('support_tickets', {}):
        await callback_query.answer("❌ Вопрос не найден!")
        return
    
    ticket_data = data['support_tickets'][ticket_id]
    
    text = f"📝 <b>Вопрос #{ticket_id}</b>\n\n"
    text += f"👤 <b>Пользователь:</b> @{ticket_data.get('username', 'N/A')}\n"
    text += f"🆔 <b>ID:</b> <code>{ticket_data.get('user_id', 'N/A')}</code>\n"
    text += f"⏰ <b>Время:</b> {ticket_data.get('timestamp', 'N/A')}\n\n"
    text += f"💬 <b>Вопрос:</b>\n{ticket_data.get('message', 'N/A')}\n\n"
    text += "👇 <b>Выберите действие:</b>"
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✏️ Ответить", callback_data=f"reply_{ticket_id}"),
        InlineKeyboardButton("✅ Решено", callback_data=f"resolve_{ticket_id}")
    )
    keyboard.add(InlineKeyboardButton("⬅️ Назад", callback_data="group_requests_questions"))
    
    await bot.send_message(
        callback_query.message.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == 'group_requests_search')
async def group_requests_search_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        InlineKeyboardButton("🎮 Standoff2", callback_data="group_search_game_standoff"),
        InlineKeyboardButton("🔲 Roblox", callback_data="group_search_game_roblox"),
        InlineKeyboardButton("⭐️ Tg star", callback_data="group_search_game_tgstar")
    )
    keyboard.add(InlineKeyboardButton("🎮 Все игры", callback_data="group_search_game_all"))
    keyboard.add(InlineKeyboardButton("⬅️ Назад", callback_data="group_back_to_requests"))
    
    await bot.send_message(
        callback_query.message.chat.id,
        "🎮 <b>Выберите игру для поиска заявки:</b>",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    
    try:
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    except:
        pass
    
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('group_search_game_'))
async def group_search_game_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    game = callback_query.data.split('_')[3]
    
    await dp.current_state(user=callback_query.from_user.id).update_data(search_game=game)
    
    game_names = {'standoff': 'Standoff 2', 'roblox': 'Roblox', 'tgstar': 'TG Star', 'all': 'Всех игр'}
    
    await bot.send_message(
        callback_query.message.chat.id,
        f"✍️ <b>Введите номер заявки для игры {game_names[game]}:</b>\n\n<i>Номер можно взять из сообщения с заявкой или из списка заявок.</i>",
        parse_mode="HTML",
        reply_markup=main_menu_reply_keyboard()
    )
    
    try:
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    except:
        pass
    
    await AdminStates.waiting_user_id.set()
    await dp.current_state(user=callback_query.from_user.id).update_data(action='search_request', from_group=True)
    
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == 'group_back_to_requests')
async def group_back_to_requests_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🍯 Выводы", callback_data="group_requests_withdraw"),
        InlineKeyboardButton("💰 Пополнения", callback_data="group_requests_purchase")
    )
    keyboard.add(
        InlineKeyboardButton("💥 Отзывы", callback_data="group_requests_reviews"),
        InlineKeyboardButton("❓ Вопросы", callback_data="group_requests_questions")
    )
    keyboard.add(InlineKeyboardButton("🔍 Найти заявку", callback_data="group_requests_search"))
    
    await bot.edit_message_text(
        "💎 <b>Выберите тип заявки:</b>",
        callback_query.message.chat.id,
        callback_query.message.message_id,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback_query.answer()

@dp.message_handler(lambda message: message.text == "📊 Статистика", chat_id=SUPPORT_GROUP_ID)
async def group_stats_button(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🎮 Standoff2", callback_data="group_stats_standoff"),
        InlineKeyboardButton("🔲 Roblox", callback_data="group_stats_roblox")
    )
    keyboard.add(
        InlineKeyboardButton("⭐️ Tg star", callback_data="group_stats_tgstar"),
        InlineKeyboardButton("📊 Все игры", callback_data="group_stats_all")
    )
    
    try:
        await message.delete()
    except:
        pass
    
    await message.answer("🔥 <b>Выберите игру для просмотра статистики</b>", parse_mode="HTML", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith('group_stats_'))
async def group_stats_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    game = callback_query.data.split('_')[2]
    data = load_data()
    stats = calculate_period_stats(data, game)
    
    current_date = datetime.now().strftime("%d.%m.%Y")
    
    game_names = {'standoff': 'Standoff 2', 'roblox': 'Roblox', 'tgstar': 'TG Star', 'all': 'Все игры'}
    game_name = game_names[game]
    
    if game == 'standoff':
        currency = 'Gold'
        purchase_currency = 'UZS'
    elif game == 'roblox':
        currency = 'Robux'
        purchase_currency = 'UZS'
    elif game == 'tgstar':
        currency = 'Stars'
        purchase_currency = 'UZS'
    else:
        currency = 'средств'
        purchase_currency = 'UZS'
    
    text = f"📊 <b>Статистика бота за {current_date}</b>\n"
    text += f"🎮 <b>Игра:</b> {game_name}\n\n"
    
    text += f"👥 <b>Пользователей:</b> {stats['total_users']:,}\n"
    text += f"├ За месяц: {stats['users_month']:,}\n"
    text += f"├ За неделю: {stats['users_week']:,}\n"
    text += f"└ За день: {stats['users_today']:,}\n\n"
    
    text += f"💵 <b>Всего пополнено:</b> {stats['total_purchase_amount']:,} {purchase_currency}\n"
    text += f"├ За месяц: {stats['purchase_amount_month']:,} {purchase_currency}\n"
    text += f"├ За неделю: {stats['purchase_amount_week']:,} {purchase_currency}\n"
    text += f"└ За день: {stats['purchase_amount_today']:,} {purchase_currency}\n\n"
    
    if game == 'all':
        text += f"🟡 <b>Выведено:</b> {stats['total_withdraw']:,}\n"
    else:
        text += f"🟡 <b>Всего выведено:</b> {stats['total_withdraw']:,} {currency}\n"
    
    text += f"├ За месяц: {stats['withdraw_month']:,}\n"
    text += f"├ За неделю: {stats['withdraw_week']:,}\n"
    text += f"└ За день: {stats['withdraw_today']:,}\n\n"
    
    text += f"💰 <b>Всего покупок:</b> {stats['total_purchases']:,}\n"
    text += f"├ За месяц: {stats['purchases_month']:,}\n"
    text += f"├ За неделю: {stats['purchases_week']:,}\n"
    text += f"└ За день: {stats['purchases_today']:,}\n\n"
    
    text += "⚙️ <b>Общие сведения:</b>\n"
    text += f"👥 За сегодня использовали бота: {stats['active_users_today']:,} чел.\n"
    
    if game == 'standoff':
        text += f"🍯 Всего {currency.lower()} у всех пользователей: {stats['total_balance_standoff']:,}\n"
    elif game == 'roblox':
        text += f"🍯 Всего {currency.lower()} у всех пользователей: {stats['total_balance_roblox']:,}\n"
    elif game == 'tgstar':
        text += f"🍯 Всего {currency.lower()} у всех пользователей: {stats['total_balance_tgstar']:,}\n"
    else:
        total_all_balance = stats['total_balance_standoff'] + stats['total_balance_roblox'] + stats['total_balance_tgstar']
        text += f"🍯 Всего средств у всех пользователей: {total_all_balance:,}\n"
    
    text += f"📖 Всего отзывов: {stats['total_reviews']:,}\n"
    text += f"🙅 Забаненных пользователей: {stats['banned_users']:,} чел.\n"
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("⬅️ Назад", callback_data="group_back_to_work"))
    
    await bot.edit_message_text(
        text,
        callback_query.message.chat.id,
        callback_query.message.message_id,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == 'group_back_to_work')
async def group_back_to_work_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    data = load_data()
    
    purchase_requests = data.get('purchase_requests', {})
    pending_purchases = sum(1 for r in purchase_requests.values() if r.get('status') == 'pending')
    
    withdraw_requests = data.get('withdraw_requests', {})
    pending_withdraws = sum(1 for r in withdraw_requests.values() if r.get('status') == 'pending')
    
    support_tickets = data.get('support_tickets', {})
    unanswered_questions = sum(1 for t in support_tickets.values() if t.get('status') in ['pending', 'in_progress'])
    
    reviews = data.get('reviews', {})
    pending_reviews = sum(1 for r in reviews.values() if r.get('status') == 'pending')
    
    text = f"🔥 <b>Режим работы</b>\n\n"
    text += f"✨ <b>Вам нужно проверить:</b>\n"
    text += f"• {pending_purchases} заявок на пополнение.\n"
    text += f"• {pending_withdraws} заявок на вывод.\n"
    text += f"• {unanswered_questions} вопросов.\n"
    text += f"• {pending_reviews} отзывов.\n\n"
    text += f"<i>Используйте кнопки ниже для работы</i>"
    
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(KeyboardButton("🛍 Заявки"), KeyboardButton("📊 Статистика"))
    keyboard.add(KeyboardButton("👑 Админ панель"))
    
    await bot.edit_message_text(
        text,
        callback_query.message.chat.id,
        callback_query.message.message_id,
        parse_mode="HTML"
    )
    
    await bot.send_message(
        callback_query.message.chat.id,
        "👇 <b>Выберите действие:</b>",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback_query.answer()

@dp.message_handler(lambda message: message.text == "👑 Админ панель", chat_id=SUPPORT_GROUP_ID)
async def group_admin_button(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📨 Рассылка", callback_data="group_admin_mailing"),
        InlineKeyboardButton("⚙️ Настройки", callback_data="group_admin_settings")
    )
    keyboard.add(
        InlineKeyboardButton("🎁 Промокоды", callback_data="group_admin_promocodes"),
        InlineKeyboardButton("💵 Оплата", callback_data="group_admin_payment")
    )
    keyboard.add(
        InlineKeyboardButton("🔎 Найти юзера", callback_data="group_admin_find_user"),
        InlineKeyboardButton("🗒 Заявки", callback_data="group_admin_requests")
    )
    keyboard.add(InlineKeyboardButton("📝 Шаблоны", callback_data="group_admin_templates"))
    
    try:
        await message.delete()
    except:
        pass
    
    await message.answer("⚡️ <b>Админ панель (Группа чеков)</b>\n👇 <b>Выберите раздел:</b>", parse_mode="HTML", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith('group_admin_'))
async def group_admin_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    action = callback_query.data.split('_')[2]
    
    if action == 'mailing':
        await admin_mailing_callback(callback_query)
    elif action == 'settings':
        await admin_settings_callback(callback_query)
    elif action == 'promocodes':
        await admin_promocodes_callback(callback_query)
    elif action == 'payment':
        await admin_payment_callback(callback_query)
    elif action == 'find_user':
        await admin_find_user_callback(callback_query)
    elif action == 'requests':
        await admin_requests_callback(callback_query)
    elif action == 'templates':
        await admin_templates_callback(callback_query)

@dp.callback_query_handler(lambda c: c.data == 'admin_back_to_main')
async def admin_back_to_main_callback(callback_query: types.CallbackQuery):
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    data = load_data()
    user_id = str(callback_query.from_user.id)
    user_data = data['users'].get(user_id, {})
    await show_game_menu(callback_query.message.chat.id, user_data.get('game', 'standoff'), user_data['username'])
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == 'admin_back')
async def admin_back_callback(callback_query: types.CallbackQuery):
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    await bot.send_message(callback_query.message.chat.id, "⚡️ <b>Админ панель успешно активирована</b>", parse_mode="HTML", reply_markup=admin_keyboard())
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == 'admin_settings')
async def admin_settings_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    await bot.send_message(callback_query.message.chat.id, "⚙️ <b>Настройки бота</b>\n👇 <b>Выберите раздел:</b>", parse_mode="HTML", reply_markup=admin_settings_keyboard())
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == 'admin_mailing')
async def admin_mailing_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    await bot.send_message(callback_query.message.chat.id, "📖 <b>Введите сообщение для рассылки:</b>", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
    await AdminStates.waiting_mailing.set()
    await callback_query.answer()

@dp.message_handler(state=AdminStates.waiting_mailing)
async def process_mailing(message: types.Message, state: FSMContext):
    if message.text == "🏠 Главное меню":
        await state.finish()
        await message.answer("⚡️ <b>Админ панель успешно активирована</b>\n", parse_mode="HTML", reply_markup=admin_keyboard())
        return
    
    mailing_text = message.text
    data = load_data()
    users = data['users']
    
    sent = 0
    failed = 0
    
    for user_id in users.keys():
        try:
            await bot.send_message(int(user_id), f"{mailing_text}", parse_mode="HTML")
            sent += 1
            await asyncio.sleep(0.05)
        except:
            failed += 1
    
    await message.answer(f"✅ <b>Рассылка завершена!</b>\n📨 Отправлено: {sent}\n❌ Не отправлено: {failed}", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'admin_find_user')
async def admin_find_user_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    await bot.send_message(callback_query.message.chat.id, "🔎 <b>Поиск пользователя</b>\n✏️ <b>Введите ID пользователя:</b>", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
    await AdminStates.waiting_user_id.set()
    await dp.current_state(chat=callback_query.message.chat.id, user=callback_query.from_user.id).update_data(action='find_user')
    await callback_query.answer()

@dp.message_handler(state=AdminStates.waiting_user_id)
async def process_user_id(message: types.Message, state: FSMContext):
    if message.text == "🏠 Главное меню":
        await state.finish()
        await message.answer("⚡️ <b>Админ панель успешно активирована</b>", parse_mode="HTML", reply_markup=admin_keyboard())
        return
    
    elif message.text == "🧳 Сменить игру":
        await state.finish()
        
        keyboard = InlineKeyboardMarkup(row_width=3)
        keyboard.add(
            InlineKeyboardButton("🎮 Standoff2", callback_data="search_game_standoff"),
            InlineKeyboardButton("🔲 Roblox", callback_data="search_game_roblox"),
            InlineKeyboardButton("⭐️ Tg star", callback_data="search_game_tgstar")
        )
        keyboard.add(InlineKeyboardButton("🎮 Все игры", callback_data="search_game_all"))
        keyboard.add(InlineKeyboardButton("⬅️ Назад", callback_data="admin_requests"))
        
        await message.answer("🎮 <b>Выберите игру для поиска заявки:</b>", parse_mode="HTML", reply_markup=keyboard)
        return
    
    request_id = message.text.strip()
    data = load_data()
    state_data = await state.get_data()
    action = state_data.get('action')
    
    if action == 'search_request':
        game = state_data.get('search_game', 'all')
        
        found_request = None
        request_type = None
        
        withdraw_requests = data.get('withdraw_requests', {})
        if request_id in withdraw_requests:
            req_data = withdraw_requests[request_id]
            if game == 'all' or req_data.get('game') == game:
                found_request = req_data
                request_type = 'withdraw'
        
        if not found_request:
            purchase_requests = data.get('purchase_requests', {})
            if request_id in purchase_requests:
                req_data = purchase_requests[request_id]
                if game == 'all' or req_data.get('game') == game:
                    found_request = req_data
                    request_type = 'purchase'
        
        if not found_request:
            reviews = data.get('reviews', {})
            if request_id in reviews:
                rev_data = reviews[request_id]
                if game == 'all' or rev_data.get('game') == game:
                    found_request = rev_data
                    request_type = 'review'
        
        if not found_request:
            await message.answer(f"❌ <b>Заявка #{request_id} не найдена.</b>\n🎮 <i>Проверьте номер и выбранную игру.</i>", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
            await state.finish()
            return
        
        user_id = found_request.get('user_id')
        user_number = get_user_number(data, user_id) if user_id in data['users'] else "N/A"
        
        if request_type == 'withdraw':
            game_name = found_request.get('game', 'standoff')
            game_names = {'standoff': 'Standoff 2', 'roblox': 'Roblox', 'tgstar': 'TG Star'}
            currency = {'standoff': 'Gold', 'roblox': 'Robux', 'tgstar': 'Stars'}[game_name]
            
            text = f"📋 <b>Заявка на вывод #{request_id}</b> <code>({user_number})</code>\n\n"
            text += f"👤 <b>Пользователь:</b> @{found_request.get('username', 'N/A')}\n"
            text += f"🆔 <b>ID:</b> <code>{user_id}</code>\n\n"
            text += f"🎮 <b>Игра:</b> {game_names[game_name]}\n"
            text += f"💰 <b>Сумма:</b> {found_request.get('amount', 0)} {currency}\n"
            
            if game_name == 'standoff':
                text += f"🏷️ <b>Цена на рынке:</b> {found_request.get('market_price', 0)} G\n"
            
            if game_name == 'tgstar' and found_request.get('receiver_username'):
                text += f"📨 <b>Получатель:</b> {found_request.get('receiver_username')}\n"
            
            text += f"⏰ <b>Время создания:</b> {found_request.get('timestamp', 'N/A')}\n"
            text += f"📊 <b>Статус:</b> {found_request.get('status', 'N/A')}\n\n"
            
            keyboard = InlineKeyboardMarkup(row_width=2)
            if found_request.get('status') == 'pending':
                keyboard.add(
                    InlineKeyboardButton("✅ Принять", callback_data=f"withdraw_accept_{request_id}"),
                    InlineKeyboardButton("❌ Отклонить", callback_data=f"withdraw_reject_{request_id}")
                )
            
        elif request_type == 'purchase':
            game_name = found_request.get('game', 'standoff')
            game_names = {'standoff': 'Standoff 2', 'roblox': 'Roblox', 'tgstar': 'TG Star'}
            currency = found_request.get('currency_name', 'Gold')
            
            text = f"🛒 <b>Заявка на покупку #{request_id}</b> <code>({user_number})</code>\n\n"
            text += f"👤 <b>Пользователь:</b> @{found_request.get('username', 'N/A')}\n"
            text += f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
            text += f"🎮 <b>Игра:</b> {game_names[game_name]}\n\n"
            text += f"💰 <b>Сумма оплаты:</b> {found_request.get('amount_uzs', 0):,} UZS\n"
            text += f"🍯 <b>Получит:</b> {found_request.get('amount_currency', 0):,} {currency}\n"
            text += f"🏦 <b>Способ оплаты:</b> {found_request.get('payment_method_bank', 'N/A')}\n\n"
            text += f"⏰ <b>Время создания:</b> {found_request.get('timestamp', 'N/A')}\n"
            text += f"📊 <b>Статус:</b> {found_request.get('status', 'N/A')}\n\n"
            
            keyboard = InlineKeyboardMarkup(row_width=2)
            if found_request.get('status') == 'pending':
                keyboard.add(
                    InlineKeyboardButton("✅ Принять", callback_data=f"purchase_accept_{request_id}"),
                    InlineKeyboardButton("❌ Отклонить", callback_data=f"purchase_reject_{request_id}")
                )
                
        elif request_type == 'review':
            game_name = found_request.get('game', 'standoff')
            game_names = {'standoff': 'Standoff 2', 'roblox': 'Roblox', 'tgstar': 'TG Star'}
            
            text = f"📝 <b>Отзыв #{request_id}</b>\n\n"
            text += f"👤 <b>Пользователь:</b> @{found_request.get('username', 'N/A')}\n"
            text += f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
            text += f"🎮 <b>Игра:</b> {game_names[game_name]}\n\n"
            text += f"⭐️ <b>Оценка:</b> {found_request.get('rating', 5)}/5\n"
            text += f"💬 <b>Текст:</b> {found_request.get('text', 'N/A')}\n\n"
            text += f"⏰ <b>Время создания:</b> {found_request.get('timestamp', 'N/A')}\n"
            text += f"📊 <b>Статус:</b> {found_request.get('status', 'N/A')}\n\n"
            
            keyboard = InlineKeyboardMarkup(row_width=2)
            if found_request.get('status') == 'pending':
                keyboard.add(
                    InlineKeyboardButton("✅ Выложить", callback_data=f"review_publish_{request_id}"),
                    InlineKeyboardButton("❌ Отклонить", callback_data=f"review_reject_{request_id}")
                )
        
        keyboard.add(InlineKeyboardButton("🔍 Искать ещё", callback_data="admin_requests"))
        keyboard.add(InlineKeyboardButton("⬅️ В меню заявок", callback_data="admin_requests"))
        
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
        await state.finish()
        return
    
    user_id = message.text.strip()
    data = load_data()
    
    if user_id not in data['users']:
        await message.answer("❌ Пользователь не найден.", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        await state.finish()
        return
    
    user_data = data['users'][user_id]
    state_data = await state.get_data()
    action = state_data.get('action')
    
    if action == 'find_user':
        text = f"👤 <b>Информация о пользователе</b>\n\n"
        text += f"✉️ <b>Ник:</b> @{user_data.get('username', 'Без имени')}\n"
        text += f"🆔 <b>ID:</b> {user_id}\n"
        text += f"🔢 <b>Номер:</b> {get_user_number(data, user_id)}\n"
        text += f"📅 <b>Регистрация:</b> {user_data.get('registration_date', 'Неизвестно')}\n"
        text += f"🚫 <b>Бан:</b> {'Да' if user_data.get('banned', False) else 'Нет'}\n\n"
        
        text += "💰 <b>Балансы:</b>\n"
        text += f"• Standoff 2: {user_data.get('balance_standoff', 0)} Gold\n"
        text += f"• Roblox: {user_data.get('balance_roblox', 0)} Robux\n"
        text += f"• TG Star: {user_data.get('balance_tgstar', 0)} Stars\n\n"
        
        text += f"🫂 <b>Рефералов:</b> {len(user_data.get('referrals', []))}\n"
        if user_data.get('referrer_id'):
            text += f"👥 <b>Пригласил:</b> @{data['users'].get(user_data['referrer_id'], {}).get('username', 'Неизвестно')}\n"
        
        if user_data.get('total_ref_earned_standoff', 0) > 0 or user_data.get('total_ref_earned_roblox', 0) > 0 or user_data.get('total_ref_earned_tgstar', 0) > 0:
            text += f"\n💰 <b>Заработано с рефералов:</b>\n"
            if user_data.get('total_ref_earned_standoff', 0) > 0:
                text += f"• Standoff 2: {user_data['total_ref_earned_standoff']} Gold\n"
            if user_data.get('total_ref_earned_roblox', 0) > 0:
                text += f"• Roblox: {user_data['total_ref_earned_roblox']} Robux\n"
            if user_data.get('total_ref_earned_tgstar', 0) > 0:
                text += f"• TG Star: {user_data['total_ref_earned_tgstar']} Stars\n"
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        if user_data.get('banned', False):
            keyboard.add(InlineKeyboardButton("🔓 Разблокировать", callback_data=f"unban_{user_id}"))
        else:
            keyboard.add(InlineKeyboardButton("🔒 Заблокировать", callback_data=f"ban_{user_id}"))
        keyboard.add(InlineKeyboardButton("✉️ Написать", callback_data=f"message_{user_id}"))
        keyboard.add(InlineKeyboardButton("💰 Баланс", callback_data=f"balance_{user_id}"))
        keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
        
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
        await state.finish()
    
    elif action in ['balance_add', 'balance_remove']:
        current_game = user_data.get('game', 'standoff')
        await state.update_data(target_user_id=user_id, target_game=current_game)
        
        currency_names = {'standoff': 'Gold', 'roblox': 'Robux', 'tgstar': 'Stars'}
        currency = currency_names[current_game]
        
        action_text = "выдачи" if action == 'balance_add' else "списания"
        
        await message.answer(f"💰 <b>Пользователь:</b> @{user_data['username']}\n🎮 <b>Игра:</b> {'Standoff 2' if current_game == 'standoff' else 'Roblox' if current_game == 'roblox' else 'TG Star'}\n💵 <b>Баланс:</b> {user_data[f'balance_{current_game}']} {currency}\n\n✏️ <b>Введите сумму для {action_text}:</b>", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        await AdminStates.waiting_user_balance.set()

@dp.callback_query_handler(lambda c: c.data.startswith(('ban_', 'unban_', 'message_', 'balance_')))
async def admin_user_actions(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    action, user_id = callback_query.data.split('_')[0], callback_query.data.split('_')[1]
    data = load_data()
    
    if user_id not in data['users']:
        await callback_query.answer("❌ Пользователь не найден!")
        return
    
    user_data = data['users'][user_id]
    
    if action == 'ban':
        data['users'][user_id]['banned'] = True
        save_data(data)
        await callback_query.answer(f"✅ Пользователь @{user_data['username']} забанен")
        
        try:
            await bot.send_message(int(user_id), "🚫 <b>Вы были забанены администратором.</b>", parse_mode="HTML")
        except:
            pass
        
    elif action == 'unban':
        data['users'][user_id]['banned'] = False
        save_data(data)
        await callback_query.answer(f"✅ Пользователь @{user_data['username']} разбанен")
        
        try:
            await bot.send_message(int(user_id), "✅ <b>Вы были разбанены администратором.</b>", parse_mode="HTML")
        except:
            pass
    
    elif action == 'message':
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
        await bot.send_message(callback_query.message.chat.id, f"✉️ <b>Написать пользователю @{user_data['username']}</b>\n✏️ <b>Введите сообщение:</b>", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        await AdminStates.waiting_user_message.set()
        await dp.current_state(chat=callback_query.message.chat.id, user=callback_query.from_user.id).update_data(target_user_id=user_id)
        await callback_query.answer()
        return
    
    elif action == 'balance':
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("➕ Выдать", callback_data=f"balance_add_{user_id}"),
            InlineKeyboardButton("➖ Забрать", callback_data=f"balance_remove_{user_id}")
        )
        keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
        
        await bot.send_message(callback_query.message.chat.id, f"💰 <b>Управление балансом @{user_data['username']}</b>\n👇 <b>Выберите действие:</b>", parse_mode="HTML", reply_markup=keyboard)
        await callback_query.answer()
        return
    
    text = f"👤 <b>Информация о пользователе</b>\n\n"
    text += f"✉️ <b>Ник:</b> @{user_data.get('username', 'Без имени')}\n"
    text += f"🆔 <b>ID:</b> {user_id}\n"
    text += f"🔢 <b>Номер:</b> {get_user_number(data, user_id)}\n"
    text += f"🚫 <b>Бан:</b> {'Да' if user_data.get('banned', False) else 'Нет'}\n\n"
    
    text += "💰 <b>Балансы:</b>\n"
    text += f"• Standoff 2: {user_data.get('balance_standoff', 0)} Gold\n"
    text += f"• Roblox: {user_data.get('balance_roblox', 0)} Robux\n"
    text += f"• TG Star: {user_data.get('balance_tgstar', 0)} Stars"
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    if user_data.get('banned', False):
        keyboard.add(InlineKeyboardButton("🔓 Разблокировать", callback_data=f"unban_{user_id}"))
    else:
        keyboard.add(InlineKeyboardButton("🔒 Заблокировать", callback_data=f"ban_{user_id}"))
    keyboard.add(InlineKeyboardButton("✉️ Написать", callback_data=f"message_{user_id}"))
    keyboard.add(InlineKeyboardButton("💰 Баланс", callback_data=f"balance_{user_id}"))
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
    
    try:
        await bot.edit_message_text(text, callback_query.message.chat.id, callback_query.message.message_id, parse_mode="HTML", reply_markup=keyboard)
    except:
        pass

@dp.callback_query_handler(lambda c: c.data.startswith(('balance_add_', 'balance_remove_')))
async def admin_balance_action_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    action = 'add' if callback_query.data.startswith('balance_add_') else 'remove'
    user_id = callback_query.data.split('_')[2]
    
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    await bot.send_message(callback_query.message.chat.id, "✏️ <b>Введите ID пользователя:</b>", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
    await AdminStates.waiting_user_id.set()
    await dp.current_state(chat=callback_query.message.chat.id, user=callback_query.from_user.id).update_data(balance_action=action, action=action)
    await callback_query.answer()

@dp.message_handler(state=AdminStates.waiting_user_balance)
async def process_user_balance(message: types.Message, state: FSMContext):
    if message.text == "🏠 Главное меню":
        await state.finish()
        await message.answer("⚡️ <b>Админ панель успешно активирована</b>", parse_mode="HTML", reply_markup=admin_keyboard())
        return
    
    try:
        amount = int(message.text)
    except:
        await message.answer("❌ Введите число.", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        return
    
    if amount <= 0:
        await message.answer("❌ Сумма должна быть > 0.", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        return
    
    state_data = await state.get_data()
    user_id = state_data.get('target_user_id')
    game = state_data.get('target_game')
    action = state_data.get('balance_action')
    
    data = load_data()
    user_data = data['users'][user_id]
    balance_field = f'balance_{game}'
    
    currency_names = {'standoff': 'Gold', 'roblox': 'Robux', 'tgstar': 'Stars'}
    currency = currency_names[game]
    
    if action == 'add':
        user_data[balance_field] += amount
        message_text = f"✅ <b>Баланс пополнен!</b>\n👤 @{user_data['username']}\n💰 +{amount} {currency}\n💵 Новый: {user_data[balance_field]} {currency}"
    else:
        if user_data[balance_field] < amount:
            await message.answer(f"❌ Недостаточно средств.\n💵 Текущий: {user_data[balance_field]} {currency}", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
            return
        user_data[balance_field] -= amount
        message_text = f"✅ <b>Баланс списан!</b>\n👤 @{user_data['username']}\n💰 -{amount} {currency}\n💵 Новый: {user_data[balance_field]} {currency}"
    
    save_data(data)
    
    try:
        await message.delete()
    except:
        pass
    
    await message.answer(message_text, parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
    await state.finish()

@dp.message_handler(state=AdminStates.waiting_user_message)
async def process_user_message(message: types.Message, state: FSMContext):
    if message.text == "🏠 Главное меню":
        await state.finish()
        await message.answer("⚡️ <b>Админ панель успешно активирована</b>\n", parse_mode="HTML", reply_markup=admin_keyboard())
        return
    
    state_data = await state.get_data()
    user_id = state_data.get('target_user_id')
    
    try:
        await bot.send_message(int(user_id), f"📨 <b>Сообщение от администратора:</b>\n\n{message.text}", parse_mode="HTML")
        await message.answer(f"✅ <b>Сообщение отправлено пользователю {user_id}</b>", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
    except:
        await message.answer(f"❌ <b>Не удалось отправить сообщение пользователю {user_id}</b>", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
    
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'admin_stats')
async def admin_stats_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🎮 Standoff2", callback_data="stats_game_standoff"),
        InlineKeyboardButton("🔲 Roblox", callback_data="stats_game_roblox")
    )
    keyboard.add(
        InlineKeyboardButton("⭐️ Tg star", callback_data="stats_game_tgstar")
    )
    keyboard.add(
        InlineKeyboardButton("📊 Статистика всех игр", callback_data="stats_game_all")
    )
    keyboard.add(
        InlineKeyboardButton("⬅️ Назад", callback_data="admin_back")
    )
    
    await bot.edit_message_text(
        "🔥 <b>Выберите игру для просмотра статистики</b>",
        callback_query.message.chat.id,
        callback_query.message.message_id,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('stats_game_'))
async def stats_game_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    game = callback_query.data.split('_')[2]
    data = load_data()
    stats = calculate_period_stats(data, game)
    
    current_date = datetime.now().strftime("%d.%m.%Y")
    
    game_names = {'standoff': 'Standoff 2', 'roblox': 'Roblox', 'tgstar': 'TG Star', 'all': 'Все игры'}
    game_name = game_names[game]
    
    if game == 'standoff':
        currency = 'Gold'
        purchase_currency = 'UZS'
    elif game == 'roblox':
        currency = 'Robux'
        purchase_currency = 'UZS'
    elif game == 'tgstar':
        currency = 'Stars'
        purchase_currency = 'UZS'
    else:
        currency = 'средств'
        purchase_currency = 'UZS'
    
    text = f"📊 <b>Статистика бота за {current_date}</b>\n"
    text += f"🎮 <b>Игра:</b> {game_name}\n\n"
    
    text += f"👥 <b>Пользователей:</b> {stats['total_users']:,}\n"
    text += f"├ За месяц: {stats['users_month']:,}\n"
    text += f"├ За неделю: {stats['users_week']:,}\n"
    text += f"└ За день: {stats['users_today']:,}\n\n"
    
    text += f"💵 <b>Всего пополнено:</b> {stats['total_purchase_amount']:,} {purchase_currency}\n"
    text += f"├ За месяц: {stats['purchase_amount_month']:,} {purchase_currency}\n"
    text += f"├ За неделю: {stats['purchase_amount_week']:,} {purchase_currency}\n"
    text += f"└ За день: {stats['purchase_amount_today']:,} {purchase_currency}\n\n"
    
    if game == 'all':
        text += f"🟡 <b>Выведено:</b> {stats['total_withdraw']:,}\n"
    else:
        text += f"🟡 <b>Всего выведено:</b> {stats['total_withdraw']:,} {currency}\n"
    
    text += f"├ За месяц: {stats['withdraw_month']:,}\n"
    text += f"├ За неделю: {stats['withdraw_week']:,}\n"
    text += f"└ За день: {stats['withdraw_today']:,}\n\n"
    
    text += f"💰 <b>Всего покупок:</b> {stats['total_purchases']:,}\n"
    text += f"├ За месяц: {stats['purchases_month']:,}\n"
    text += f"├ За неделю: {stats['purchases_week']:,}\n"
    text += f"└ За день: {stats['purchases_today']:,}\n\n"
    
    text += "⚙️ <b>Общие сведения:</b>\n"
    text += f"👥 За сегодня использовали бота: {stats['active_users_today']:,} чел.\n"
    
    if game == 'standoff':
        text += f"🍯 Всего {currency.lower()} у всех пользователей: {stats['total_balance_standoff']:,}\n"
    elif game == 'roblox':
        text += f"🍯 Всего {currency.lower()} у всех пользователей: {stats['total_balance_roblox']:,}\n"
    elif game == 'tgstar':
        text += f"🍯 Всего {currency.lower()} у всех пользователей: {stats['total_balance_tgstar']:,}\n"
    else:
        total_all_balance = stats['total_balance_standoff'] + stats['total_balance_roblox'] + stats['total_balance_tgstar']
        text += f"🍯 Всего средств у всех пользователей: {total_all_balance:,}\n"
    
    text += f"📖 Всего отзывов: {stats['total_reviews']:,}\n"
    text += f"🙅 Забаненных пользователей: {stats['banned_users']:,} чел.\n"
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_stats"))
    
    await bot.edit_message_text(
        text,
        callback_query.message.chat.id,
        callback_query.message.message_id,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == 'admin_tops')
async def admin_tops_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    data = load_data()
    users = data['users']
    
    standoff_users = []
    for user_id, user_data in users.items():
        if 'total_earned_standoff' in user_data and user_data['total_earned_standoff'] > 0:
            standoff_users.append((user_data['username'], user_data['total_earned_standoff']))
    
    standoff_users.sort(key=lambda x: x[1], reverse=True)
    standoff_top = standoff_users[:5]
    
    roblox_users = []
    for user_id, user_data in users.items():
        if 'total_earned_roblox' in user_data and user_data['total_earned_roblox'] > 0:
            roblox_users.append((user_data['username'], user_data['total_earned_roblox']))
    
    roblox_users.sort(key=lambda x: x[1], reverse=True)
    roblox_top = roblox_users[:5]
    
    tgstar_users = []
    for user_id, user_data in users.items():
        if 'total_earned_tgstar' in user_data and user_data['total_earned_tgstar'] > 0:
            tgstar_users.append((user_data['username'], user_data['total_earned_tgstar']))
    
    tgstar_users.sort(key=lambda x: x[1], reverse=True)
    tgstar_top = tgstar_users[:5]
    
    ref_users = []
    for user_id, user_data in users.items():
        total_ref = user_data.get('total_ref_earned_standoff', 0) + user_data.get('total_ref_earned_roblox', 0) + user_data.get('total_ref_earned_tgstar', 0)
        if total_ref > 0:
            ref_users.append((user_data['username'], total_ref, len(user_data.get('referrals', []))))
    
    ref_users.sort(key=lambda x: x[1], reverse=True)
    ref_top = ref_users[:5]
    
    text = "🏆 <b>Топ пользователей</b>\n\n"
    
    text += "🎮 <b>Standoff 2 (Gold):</b>\n"
    if standoff_top:
        for i, (username, amount) in enumerate(standoff_top, 1):
            text += f"{i}. @{username} - {amount} Gold\n"
    else:
        text += "Нет данных\n"
    
    text += "\n🌟 <b>Roblox (Robux):</b>\n"
    if roblox_top:
        for i, (username, amount) in enumerate(roblox_top, 1):
            text += f"{i}. @{username} - {amount} Robux\n"
    else:
        text += "Нет данных\n"
    
    text += "\n⭐️ <b>TG Star (Stars):</b>\n"
    if tgstar_top:
        for i, (username, amount) in enumerate(tgstar_top, 1):
            text += f"{i}. @{username} - {amount} Stars\n"
    else:
        text += "Нет данных\n"
    
    text += "\n💌 <b>Топ рефералов:</b>\n"
    if ref_top:
        for i, (username, amount, ref_count) in enumerate(ref_top, 1):
            text += f"{i}. @{username} - {amount} заработано ({ref_count} реф.)\n"
    else:
        text += "Нет данных\n"
    
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    await bot.send_message(callback_query.message.chat.id, text, parse_mode="HTML", reply_markup=admin_settings_keyboard())
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == 'admin_requests')
async def admin_requests_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🍯 Выводы", callback_data="requests_withdraw"),
        InlineKeyboardButton("💰 Пополнения", callback_data="requests_purchase")
    )
    keyboard.add(
        InlineKeyboardButton("💥 Отзывы", callback_data="requests_reviews"),
        InlineKeyboardButton("🔍 Найти заявку", callback_data="requests_search")
    )
    keyboard.add(InlineKeyboardButton("⬅️ Назад", callback_data="admin_back"))
    
    await bot.edit_message_text(
        "💎 <b>Выберите тип заявки:</b>",
        callback_query.message.chat.id,
        callback_query.message.message_id,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == 'requests_withdraw')
async def requests_withdraw_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        InlineKeyboardButton("🎮 Standoff2", callback_data="withdraw_game_standoff"),
        InlineKeyboardButton("🔲 Roblox", callback_data="withdraw_game_roblox"),
        InlineKeyboardButton("⭐️ Tg star", callback_data="withdraw_game_tgstar")
    )
    keyboard.add(InlineKeyboardButton("⬅️ Назад", callback_data="admin_requests"))
    
    await bot.edit_message_text(
        "🤩 <b>Выберите игру:</b>",
        callback_query.message.chat.id,
        callback_query.message.message_id,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('withdraw_game_'))
async def withdraw_game_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    game = callback_query.data.split('_')[2]
    data = load_data()
    withdraw_requests = data.get('withdraw_requests', {})
    
    pending_requests = {}
    for req_id, req_data in withdraw_requests.items():
        if req_data.get('game') == game and req_data.get('status') == 'pending':
            pending_requests[req_id] = req_data
    
    if not pending_requests:
        await callback_query.answer("📭 Нет непроверенных заявок на вывод!")
        return
    
    game_names = {'standoff': 'Standoff 2', 'roblox': 'Roblox', 'tgstar': 'TG Star'}
    currency = {'standoff': 'Gold', 'roblox': 'Robux', 'tgstar': 'Stars'}[game]
    
    text = f"🍯 <b>Выберите действие:</b>\n"
    text += f"🎮 <b>Игра:</b> {game_names[game]}\n"
    text += f"📊 <b>Непроверенных заявок:</b> {len(pending_requests)}\n\n"
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    for req_id, req_data in list(pending_requests.items())[:20]:
        amount = req_data.get('amount', 0)
        if game == 'standoff':
            btn_text = f"💥 #{req_id} | {amount}G"
        elif game == 'roblox':
            btn_text = f"💥 #{req_id} | {amount} RBX"
        else:
            btn_text = f"💥 #{req_id} | {amount} ⭐"
        
        keyboard.add(InlineKeyboardButton(btn_text, callback_data=f"view_withdraw_{req_id}"))
    
    keyboard.add(InlineKeyboardButton("⬅️ Назад", callback_data="requests_withdraw"))
    
    await bot.edit_message_text(
        text,
        callback_query.message.chat.id,
        callback_query.message.message_id,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('view_withdraw_'))
async def view_withdraw_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    request_id = callback_query.data.split('_')[2]
    data = load_data()
    
    if request_id not in data.get('withdraw_requests', {}):
        await callback_query.answer("❌ Заявка не найдена!")
        return
    
    request_data = data['withdraw_requests'][request_id]
    user_id = request_data.get('user_id')
    user_number = get_user_number(data, user_id) if user_id in data['users'] else "N/A"
    
    game = request_data.get('game', 'standoff')
    game_names = {'standoff': 'Standoff 2', 'roblox': 'Roblox', 'tgstar': 'TG Star'}
    currency = {'standoff': 'Gold', 'roblox': 'Robux', 'tgstar': 'Stars'}[game]
    
    caption = f"📋 <b>Заявка на вывод #{request_id}</b> <code>({user_number})</code>\n\n"
    caption += f"👤 <b>Пользователь:</b> @{request_data.get('username', 'N/A')}\n"
    caption += f"🆔 <b>ID:</b> <code>{user_id}</code>\n\n"
    caption += f"🎮 <b>Игра:</b> {game_names[game]}\n"
    caption += f"💰 <b>Сумма:</b> {request_data.get('amount', 0)} {currency}\n"
    
    if game == 'standoff':
        caption += f"🏷️ <b>Цена на рынке:</b> {request_data.get('market_price', 0)} G\n"
    
    if game == 'roblox':
        caption += f"🎮 <b>Способ:</b> {request_data.get('method', 'N/A')}\n"
        if request_data.get('gamepass_id'):
            caption += f"🆔 <b>GamePass ID:</b> <code>{request_data.get('gamepass_id')}</code>\n"
        if request_data.get('credentials'):
            creds = request_data['credentials'].split(':')
            if len(creds) >= 2:
                caption += f"👤 <b>Логин:</b> <code>{creds[0]}</code>\n"
                caption += f"🔐 <b>Пароль:</b> <code>{creds[1][:3]}...</code>\n"
    
    if game == 'tgstar' and request_data.get('receiver_username'):
        caption += f"📨 <b>Получатель:</b> {request_data.get('receiver_username')}\n"
    
    caption += f"⏰ <b>Время создания:</b> {request_data.get('timestamp', 'N/A')}\n"
    caption += f"📊 <b>Статус:</b> {'⏳ Ожидает' if request_data.get('status') == 'pending' else '✅ Принята' if request_data.get('status') == 'completed' else '❌ Отклонена'}\n\n"
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    if request_data.get('status') == 'pending':
        keyboard.add(
            InlineKeyboardButton("✅ Принять", callback_data=f"withdraw_accept_{request_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"withdraw_reject_{request_id}")
        )
    
    keyboard.add(InlineKeyboardButton("⬅️ Назад", callback_data=f"withdraw_game_{game}"))
    
    if request_data.get('screenshot_file_id') and game == 'standoff':
        try:
            await bot.send_photo(
                callback_query.message.chat.id,
                request_data['screenshot_file_id'],
                caption=caption,
                parse_mode="HTML",
                reply_markup=keyboard
            )
            try:
                await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
            except:
                pass
        except:
            await bot.send_message(
                callback_query.message.chat.id,
                f"{caption}\n\n❌ <i>Не удалось загрузить скриншот</i>",
                parse_mode="HTML",
                reply_markup=keyboard
            )
    else:
        await bot.edit_message_text(
            caption,
            callback_query.message.chat.id,
            callback_query.message.message_id,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == 'requests_purchase')
async def requests_purchase_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    data = load_data()
    purchase_requests = data.get('purchase_requests', {})
    
    pending_requests = {}
    for req_id, req_data in purchase_requests.items():
        if req_data.get('status') == 'pending':
            pending_requests[req_id] = req_data
    
    if not pending_requests:
        await callback_query.answer("📭 Нет непроверенных заявок на пополнение!")
        return
    
    text = f"💰 <b>Заявки на пополнение</b>\n"
    text += f"📊 <b>Непроверенных заявок:</b> {len(pending_requests)}\n\n"
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    for req_id, req_data in list(pending_requests.items())[:20]:
        game = req_data.get('game', 'standoff')
        currency = {'standoff': 'Gold', 'roblox': 'Robux', 'tgstar': 'Stars'}[game]
        
        amount_currency = req_data.get('amount_currency', 0)
        amount_uzs = req_data.get('amount_uzs', 0)
        
        btn_text = f"🛒 #{req_id} | {amount_currency} {currency} | {amount_uzs:,} UZS"
        keyboard.add(InlineKeyboardButton(btn_text, callback_data=f"view_purchase_{req_id}"))
    
    keyboard.add(InlineKeyboardButton("⬅️ Назад", callback_data="admin_requests"))
    
    await bot.edit_message_text(
        text,
        callback_query.message.chat.id,
        callback_query.message.message_id,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('view_purchase_'))
async def view_purchase_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    request_id = callback_query.data.split('_')[2]
    data = load_data()
    
    if request_id not in data.get('purchase_requests', {}):
        await callback_query.answer("❌ Заявка не найдена!")
        return
    
    request_data = data['purchase_requests'][request_id]
    user_id = request_data.get('user_id')
    user_number = get_user_number(data, user_id) if user_id in data['users'] else "N/A"
    
    game = request_data.get('game', 'standoff')
    game_names = {'standoff': 'Standoff 2', 'roblox': 'Roblox', 'tgstar': 'TG Star'}
    currency = request_data.get('currency_name', 'Gold')
    
    caption = f"🛒 <b>Заявка на покупку #{request_id}</b> <code>({user_number})</code>\n\n"
    caption += f"👤 <b>Пользователь:</b> @{request_data.get('username', 'N/A')}\n"
    caption += f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
    caption += f"🎮 <b>Игра:</b> {game_names[game]}\n\n"
    caption += f"💰 <b>Сумма оплаты:</b> {request_data.get('amount_uzs', 0):,} UZS\n"
    caption += f"🍯 <b>Получит:</b> {request_data.get('amount_currency', 0):,} {currency}\n"
    caption += f"🏦 <b>Способ оплаты:</b> {request_data.get('payment_method_bank', 'N/A')}\n\n"
    caption += f"⏰ <b>Время создания:</b> {request_data.get('timestamp', 'N/A')}\n"
    caption += f"📊 <b>Статус:</b> {'⏳ Ожидает' if request_data.get('status') == 'pending' else '✅ Принята' if request_data.get('status') == 'completed' else '❌ Отклонена'}\n\n"
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    if request_data.get('status') == 'pending':
        keyboard.add(
            InlineKeyboardButton("✅ Принять", callback_data=f"purchase_accept_{request_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"purchase_reject_{request_id}")
        )
    
    keyboard.add(InlineKeyboardButton("⬅️ Назад", callback_data="requests_purchase"))
    
    if request_data.get('screenshot_file_id'):
        try:
            await bot.send_photo(
                callback_query.message.chat.id,
                request_data['screenshot_file_id'],
                caption=caption,
                parse_mode="HTML",
                reply_markup=keyboard
            )
            try:
                await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
            except:
                pass
        except:
            await bot.send_message(
                callback_query.message.chat.id,
                f"{caption}\n\n❌ <i>Не удалось загрузить скриншот чека</i>",
                parse_mode="HTML",
                reply_markup=keyboard
            )
    else:
        await bot.edit_message_text(
            caption,
            callback_query.message.chat.id,
            callback_query.message.message_id,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == 'requests_reviews')
async def requests_reviews_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    data = load_data()
    reviews = data.get('reviews', {})
    
    pending_reviews = {}
    for rev_id, rev_data in reviews.items():
        if rev_data.get('status') == 'pending':
            pending_reviews[rev_id] = rev_data
    
    if not pending_reviews:
        await callback_query.answer("📭 Нет отзывов на модерации!")
        return
    
    text = f"💥 <b>Отзывы на модерации</b>\n"
    text += f"📊 <b>Отзывов на проверке:</b> {len(pending_reviews)}\n\n"
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    for rev_id, rev_data in list(pending_reviews.items())[:20]:
        game = rev_data.get('game', 'standoff')
        game_names = {'standoff': 'Standoff 2', 'roblox': 'Roblox', 'tgstar': 'TG Star'}
        rating = rev_data.get('rating', 5)
        
        btn_text = f"⭐ #{rev_id} | {rating}/5 | {game_names.get(game, game)}"
        keyboard.add(InlineKeyboardButton(btn_text, callback_data=f"view_review_{rev_id}"))
    
    keyboard.add(InlineKeyboardButton("⬅️ Назад", callback_data="admin_requests"))
    
    await bot.edit_message_text(
        text,
        callback_query.message.chat.id,
        callback_query.message.message_id,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == 'requests_search')
async def requests_search_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        InlineKeyboardButton("🎮 Standoff2", callback_data="search_game_standoff"),
        InlineKeyboardButton("🔲 Roblox", callback_data="search_game_roblox"),
        InlineKeyboardButton("⭐️ Tg star", callback_data="search_game_tgstar")
    )
    keyboard.add(InlineKeyboardButton("🎮 Все игры", callback_data="search_game_all"))
    keyboard.add(InlineKeyboardButton("⬅️ Назад", callback_data="admin_requests"))
    
    await bot.edit_message_text(
        "🎮 <b>Выберите игру для поиска заявки:</b>",
        callback_query.message.chat.id,
        callback_query.message.message_id,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('search_game_'))
async def search_game_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    game = callback_query.data.split('_')[2]
    
    await dp.current_state(user=callback_query.from_user.id).update_data(search_game=game)
    
    game_names = {'standoff': 'Standoff 2', 'roblox': 'Roblox', 'tgstar': 'TG Star', 'all': 'Всех игр'}
    
    reply_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    reply_keyboard.add(KeyboardButton("🧳 Сменить игру"), KeyboardButton("🏠 Главное меню"))
    
    await bot.edit_message_text(
        f"✍️ <b>Введите номер заявки (вывода/пополнения/отзыва) для просмотра.</b>\n🎮 <b>Игра:</b> {game_names[game]}",
        callback_query.message.chat.id,
        callback_query.message.message_id,
        parse_mode="HTML"
    )
    
    await bot.send_message(
        callback_query.message.chat.id,
        "👇 <b>Используйте кнопки ниже:</b>",
        parse_mode="HTML",
        reply_markup=reply_keyboard
    )
    
    await AdminStates.waiting_user_id.set()
    await dp.current_state(user=callback_query.from_user.id).update_data(action='search_request')
    
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == 'ref_system')
async def ref_system_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    data = load_data()
    ref_settings = data['referral_settings']
    
    text = "💌 <b>Реферальная система</b>\n\n"
    text += f"🎮 <b>Проценты:</b>\n"
    text += f"• Standoff 2: {ref_settings.get('standoff_percent', 10)}%\n"
    text += f"• Roblox: {ref_settings.get('roblox_percent', 10)}%\n"
    text += f"• TG Star: {ref_settings.get('tgstar_percent', 10)}%\n\n"
    text += "✏️ <b>Введите процент для игры (например: standoff 15):</b>"
    
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    await bot.send_message(callback_query.message.chat.id, text, parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
    await AdminStates.waiting_ref_percent.set()
    await callback_query.answer()

@dp.message_handler(state=AdminStates.waiting_ref_percent)
async def process_ref_percent(message: types.Message, state: FSMContext):
    if message.text == "🏠 Главное меню":
        await state.finish()
        await message.answer("⚡️ <b>Админ панель успешно активирована</b>", parse_mode="HTML", reply_markup=admin_keyboard())
        return
    
    parts = message.text.strip().split()
    if len(parts) != 2:
        await message.answer("❌ Формат: <игра> <процент>\nПример: standoff 15", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        return
    
    game, percent_str = parts[0].lower(), parts[1]
    
    if game not in ['standoff', 'roblox', 'tgstar']:
        await message.answer("❌ Игра должна быть: standoff, roblox или tgstar", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        return
    
    try:
        percent = int(percent_str)
    except:
        await message.answer("❌ Процент должен быть числом.", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        return
    
    if percent < 0 or percent > 100:
        await message.answer("❌ Процент должен быть от 0 до 100.", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        return
    
    data = load_data()
    data['referral_settings'][f'{game}_percent'] = percent
    save_data(data)
    
    game_names = {'standoff': 'Standoff 2', 'roblox': 'Roblox', 'tgstar': 'TG Star'}
    
    await message.answer(f"✅ <b>Процент для {game_names[game]} установлен: {percent}%</b>", parse_mode="HTML", reply_markup=admin_settings_keyboard())
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'exchange_rates')
async def exchange_rates_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    data = load_data()
    rates = data['settings']['exchange_rates']
    
    text = "💱 <b>Курсы обмена</b>\n\n"
    text += f"🎮 <b>Текущие курсы:</b>\n"
    text += f"• Standoff 2 (Gold): 1 Gold = {rates.get('standoff', 125):,} UZS\n"
    text += f"• Roblox (Robux): 1 Robux = {rates.get('roblox', 149):,} UZS\n"
    text += f"• TG Star (Stars): 1 Star = {rates.get('tgstar', 260):,} UZS\n\n"
    text += "✏️ <b>Введите курс для игры (например: standoff 130):</b>"
    
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    await bot.send_message(callback_query.message.chat.id, text, parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
    await AdminStates.waiting_exchange_rate.set()
    await callback_query.answer()

@dp.message_handler(state=AdminStates.waiting_exchange_rate)
async def process_exchange_rate(message: types.Message, state: FSMContext):
    if message.text == "🏠 Главное меню":
        await state.finish()
        await message.answer("⚡️ <b>Админ панель успешно активирована</b>", parse_mode="HTML", reply_markup=admin_keyboard())
        return
    
    parts = message.text.strip().split()
    if len(parts) != 2:
        await message.answer("❌ Формат: <игра> <курс>\nПример: standoff 130", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        return
    
    game, rate_str = parts[0].lower(), parts[1]
    
    if game not in ['standoff', 'roblox', 'tgstar']:
        await message.answer("❌ Игра должна быть: standoff, roblox или tgstar", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        return
    
    try:
        rate = int(rate_str)
    except:
        await message.answer("❌ Курс должен быть числом.", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        return
    
    if rate <= 0:
        await message.answer("❌ Курс должен быть > 0.", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        return
    
    data = load_data()
    data['settings']['exchange_rates'][game] = rate
    save_data(data)
    
    game_names = {'standoff': 'Standoff 2', 'roblox': 'Roblox', 'tgstar': 'TG Star'}
    
    await message.answer(f"✅ <b>Курс для {game_names[game]} установлен: 1 = {rate:,} UZS</b>", parse_mode="HTML", reply_markup=admin_settings_keyboard())
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'admin_limits')
async def admin_limits_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    data = load_data()
    settings = data['settings']
    
    text = "⚡️ <b>Лимиты</b>\n\n"
    text += f"🛒 <b>Лимиты покупки:</b>\n"
    text += f"• Мин. покупка: {settings['min_purchase']:,} UZS\n"
    text += f"• Макс. покупка: {settings['max_purchase']:,} UZS\n\n"
    
    text += f"💸 <b>Лимиты вывода:</b>\n"
    text += f"• Standoff 2: {settings['min_withdraw']['standoff']} - {settings['max_withdraw']['standoff']} Gold\n"
    text += f"• Roblox: {settings['min_withdraw']['roblox']} - {settings['max_withdraw']['roblox']} Robux\n"
    text += f"• TG Star: {settings['min_withdraw']['tgstar']} - {settings['max_withdraw']['tgstar']} Stars\n\n"
    
    text += f"🏷️ <b>Множитель Standoff:</b> {settings['withdraw_multiplier']}\n\n"
    text += "✏️ <b>Выберите что изменить:</b>"
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🛒 Лимиты покупки", callback_data="limits_purchase"),
        InlineKeyboardButton("💸 Лимиты вывода", callback_data="limits_withdraw")
    )
    keyboard.add(
        InlineKeyboardButton("🔙 Назад", callback_data="admin_back")
    )
    
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    await bot.send_message(callback_query.message.chat.id, text, parse_mode="HTML", reply_markup=keyboard)
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('limits_'))
async def limits_type_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    limit_type = callback_query.data.split('_')[1]
    
    if limit_type == 'purchase':
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
        await bot.send_message(callback_query.message.chat.id, "✏️ <b>Введите мин. и макс. сумму покупки (например: 100000 5000000):</b>", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        await AdminStates.waiting_min_max_value.set()
        await dp.current_state(chat=callback_query.message.chat.id, user=callback_query.from_user.id).update_data(limit_type='purchase')
    
    elif limit_type == 'withdraw':
        keyboard = InlineKeyboardMarkup(row_width=3)
        keyboard.add(
            InlineKeyboardButton("🎮 Standoff 2", callback_data="withdraw_limits_standoff"),
            InlineKeyboardButton("🔳 Roblox", callback_data="withdraw_limits_roblox"),
            InlineKeyboardButton("⭐️ TG Star", callback_data="withdraw_limits_tgstar")
        )
        keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_limits"))
        
        await bot.edit_message_text("👇 <b>Выберите игру для изменения лимитов вывода:</b>", callback_query.message.chat.id, callback_query.message.message_id, parse_mode="HTML", reply_markup=keyboard)
    
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('withdraw_limits_'))
async def withdraw_limits_game_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    game = callback_query.data.split('_')[2]
    
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    await bot.send_message(callback_query.message.chat.id, f"✏️ <b>Введите мин. и макс. сумму вывода для {game} (например: 50 10000):</b>", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
    await AdminStates.waiting_min_max_value.set()
    await dp.current_state(chat=callback_query.message.chat.id, user=callback_query.from_user.id).update_data(limit_type=f'withdraw_{game}')
    await callback_query.answer()

@dp.message_handler(state=AdminStates.waiting_min_max_value)
async def process_min_max_value(message: types.Message, state: FSMContext):
    if message.text == "🏠 Главное меню":
        await state.finish()
        await message.answer("⚡️ <b>Админ панель успешно активирована</b>", parse_mode="HTML", reply_markup=admin_keyboard())
        return
    
    state_data = await state.get_data()
    limit_type = state_data.get('limit_type')
    data = load_data()
    
    if limit_type == 'purchase':
        parts = message.text.strip().split()
        if len(parts) != 2:
            await message.answer("❌ Формат: <мин> <макс>\nПример: 100000 5000000", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
            return
        
        try:
            min_val = int(parts[0])
            max_val = int(parts[1])
        except:
            await message.answer("❌ Оба значения должны быть числами.", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
            return
        
        if min_val <= 0 or max_val <= 0:
            await message.answer("❌ Значения должны быть > 0.", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
            return
        
        if min_val >= max_val:
            await message.answer("❌ Мин. значение должно быть меньше макс.", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
            return
        
        data['settings']['min_purchase'] = min_val
        data['settings']['max_purchase'] = max_val
        save_data(data)
        
        await message.answer(f"✅ <b>Лимиты покупки обновлены:</b>\n🛒 Мин.: {min_val:,} UZS\n📈 Макс.: {max_val:,} UZS", parse_mode="HTML", reply_markup=admin_settings_keyboard())
    
    elif limit_type.startswith('withdraw_'):
        game = limit_type.split('_')[1]
        parts = message.text.strip().split()
        
        if len(parts) != 2:
            await message.answer("❌ Формат: <мин> <макс>\nПример: 50 10000", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
            return
        
        try:
            min_val = int(parts[0])
            max_val = int(parts[1])
        except:
            await message.answer("❌ Оба значения должны быть числами.", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
            return
        
        if min_val <= 0 or max_val <= 0:
            await message.answer("❌ Значения должны быть > 0.", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
            return
        
        if min_val >= max_val:
            await message.answer("❌ Мин. значение должно быть меньше макс.", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
            return
        
        data['settings']['min_withdraw'][game] = min_val
        data['settings']['max_withdraw'][game] = max_val
        save_data(data)
        
        game_names = {'standoff': 'Standoff 2', 'roblox': 'Roblox', 'tgstar': 'TG Star'}
        currency = {'standoff': 'Gold', 'roblox': 'Robux', 'tgstar': 'Stars'}[game]
        
        await message.answer(f"✅ <b>Лимиты вывода для {game_names[game]} обновлены:</b>\n💸 Мин.: {min_val} {currency}\n📈 Макс.: {max_val} {currency}", parse_mode="HTML", reply_markup=admin_settings_keyboard())
    
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'admin_payment')
async def admin_payment_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    payment_data = load_payment_methods()
    methods = payment_data['methods']
    
    text = "💵 <b>Способы оплаты</b>\n\n"
    
    if methods:
        for method in methods:
            text += f"🏦 <b>{method['bank_name']}</b>\n"
            text += f"👤 {method['recipient_name']}\n"
            if method.get('card'):
                text += f"💳 {method['card']}\n"
            if method.get('phone'):
                text += f"📱 {method['phone']}\n"
            game = method['game']
            game_name = {'standoff': 'Standoff 2', 'roblox': 'Roblox', 'tgstar': 'TG Star', 'all': 'Все игры'}[game]
            text += f"🎮 {game_name}\n"
            text += f"🆔 ID: {method['id']}\n\n"
    else:
        text += "❌ Нет способов оплаты.\n"
    
    text += "👇 <b>Выберите действие:</b>"
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("➕ Добавить", callback_data="payment_add"),
        InlineKeyboardButton("🗑️ Удалить", callback_data="payment_delete")
    )
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
    
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    await bot.send_message(callback_query.message.chat.id, text, parse_mode="HTML", reply_markup=keyboard)
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == 'payment_add')
async def payment_add_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        InlineKeyboardButton("🎮 Standoff 2", callback_data="payment_game_standoff"),
        InlineKeyboardButton("🌟 Roblox", callback_data="payment_game_roblox"),
        InlineKeyboardButton("⭐️ TG Star", callback_data="payment_game_tgstar")
    )
    keyboard.add(InlineKeyboardButton("🎮 Все игры", callback_data="payment_game_all"))
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_payment"))
    
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    await bot.send_message(callback_query.message.chat.id, "👇 <b>Выберите игру для способа оплаты:</b>", parse_mode="HTML", reply_markup=keyboard)
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('payment_game_'))
async def payment_game_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    game = callback_query.data.split('_')[2]
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    await bot.send_message(callback_query.message.chat.id, "✏️ <b>Введите название банка:</b>", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
    await AdminStates.waiting_payment_method_bank.set()
    await dp.current_state(chat=callback_query.message.chat.id, user=callback_query.from_user.id).update_data(payment_game=game)
    await callback_query.answer()

@dp.message_handler(state=AdminStates.waiting_payment_method_bank)
async def process_payment_bank(message: types.Message, state: FSMContext):
    if message.text == "🏠 Главное меню":
        await state.finish()
        await message.answer("⚡️ <b>Админ панель успешно активирована</b>", parse_mode="HTML", reply_markup=admin_keyboard())
        return
    
    await state.update_data(bank_name=message.text)
    await message.answer("✏️ <b>Введите имя получателя:</b>", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
    await AdminStates.waiting_payment_method_recipient.set()

@dp.message_handler(state=AdminStates.waiting_payment_method_recipient)
async def process_payment_recipient(message: types.Message, state: FSMContext):
    if message.text == "🏠 Главное меню":
        await state.finish()
        await message.answer("⚡️ <b>Админ панель</b>\n👇 <b>Выберите раздел:</b>", parse_mode="HTML", reply_markup=admin_keyboard())
        return
    
    await state.update_data(recipient_name=message.text)
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("💳 Карта", callback_data="payment_type_card"),
        InlineKeyboardButton("📱 Телефон", callback_data="payment_type_phone")
    )
    keyboard.add(InlineKeyboardButton("✖️ Пропустить", callback_data="payment_type_skip"))
    
    await message.answer("👇 <b>Выберите тип реквизитов (или пропустите):</b>", parse_mode="HTML", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith('payment_type_'), state='*')
async def payment_type_callback(callback_query: types.CallbackQuery, state: FSMContext):
    payment_type = callback_query.data.split('_')[2]
    
    if payment_type == 'card':
        await bot.send_message(callback_query.message.chat.id, "✏️ <b>Введите номер карты:</b>", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        await AdminStates.waiting_payment_method_card.set()
    
    elif payment_type == 'phone':
        await bot.send_message(callback_query.message.chat.id, "✏️ <b>Введите номер телефона:</b>", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        await AdminStates.waiting_payment_method_phone.set()
    
    elif payment_type == 'skip':
        payment_data = load_payment_methods()
        state_data = await state.get_data()
        
        new_method = {
            'id': payment_data['next_id'],
            'bank_name': state_data['bank_name'],
            'recipient_name': state_data['recipient_name'],
            'game': state_data['payment_game']
        }
        
        payment_data['methods'].append(new_method)
        payment_data['next_id'] += 1
        save_payment_methods(payment_data)
        
        await bot.send_message(callback_query.message.chat.id, "✅ <b>Способ оплаты добавлен!</b>", parse_mode="HTML")
        await state.finish()
    
    await callback_query.answer()

@dp.message_handler(state=AdminStates.waiting_payment_method_card)
async def process_payment_card(message: types.Message, state: FSMContext):
    if message.text == "🏠 Главное меню":
        await state.finish()
        await message.answer("⚡️ <b>Админ панель успешно активирована</b>", parse_mode="HTML", reply_markup=admin_keyboard())
        return
    
    payment_data = load_payment_methods()
    state_data = await state.get_data()
    
    new_method = {
        'id': payment_data['next_id'],
        'bank_name': state_data['bank_name'],
        'recipient_name': state_data['recipient_name'],
        'card': message.text,
        'game': state_data['payment_game']
    }
    
    payment_data['methods'].append(new_method)
    payment_data['next_id'] += 1
    save_payment_methods(payment_data)
    
    await message.answer("✅ <b>Способ оплаты с картой добавлен!</b>", parse_mode="HTML")
    await state.finish()

@dp.message_handler(state=AdminStates.waiting_payment_method_phone)
async def process_payment_phone(message: types.Message, state: FSMContext):
    if message.text == "🏠 Главное меню":
        await state.finish()
        await message.answer("⚡️ <b>Админ панель успешно активирована</b>", parse_mode="HTML", reply_markup=admin_keyboard())
        return
    
    payment_data = load_payment_methods()
    state_data = await state.get_data()
    
    new_method = {
        'id': payment_data['next_id'],
        'bank_name': state_data['bank_name'],
        'recipient_name': state_data['recipient_name'],
        'phone': message.text,
        'game': state_data['payment_game']
    }
    
    payment_data['methods'].append(new_method)
    payment_data['next_id'] += 1
    save_payment_methods(payment_data)
    
    await message.answer("✅ <b>Способ оплаты с телефоном добавлен!</b>", parse_mode="HTML")
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'payment_delete')
async def payment_delete_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    payment_data = load_payment_methods()
    
    if not payment_data['methods']:
        await callback_query.answer("❌ Нет способов оплаты для удаления!")
        return
    
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    await bot.send_message(callback_query.message.chat.id, "✏️ <b>Введите ID способа оплаты для удаления:</b>", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
    await AdminStates.waiting_delete_payment_method.set()
    await callback_query.answer()

@dp.message_handler(state=AdminStates.waiting_delete_payment_method)
async def process_delete_payment_method(message: types.Message, state: FSMContext):
    if message.text == "🏠 Главное меню":
        await state.finish()
        await message.answer("⚡️ <b>Админ панель успешно активирована</b>", parse_mode="HTML", reply_markup=admin_keyboard())
        return
    
    try:
        method_id = int(message.text)
    except:
        await message.answer("❌ Введите число (ID).", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        return
    
    payment_data = load_payment_methods()
    
    method_to_delete = None
    for i, method in enumerate(payment_data['methods']):
        if method['id'] == method_id:
            method_to_delete = method
            del payment_data['methods'][i]
            break
    
    if not method_to_delete:
        await message.answer("❌ Способ оплаты с таким ID не найден.", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        await state.finish()
        return
    
    save_payment_methods(payment_data)
    
    await message.answer(f"✅ <b>Способ оплаты удален:</b>\n🏦 {method_to_delete['bank_name']}\n👤 {method_to_delete['recipient_name']}", parse_mode="HTML")
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'admin_promocodes')
async def admin_promocodes_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    data = load_data()
    promocodes = data.get('promocodes', {})
    
    text = "🎁 <b>Промокоды</b>\n\n"
    
    if promocodes:
        for code, code_data in promocodes.items():
            text += f"• <b>{code}</b> - {code_data.get('bonus', 0)}"
            game = code_data.get('game', 'all')
            if game == 'standoff':
                text += " Gold"
            elif game == 'roblox':
                text += " Robux"
            elif game == 'tgstar':
                text += " Stars"
            else:
                text += " (все игры)"
            
            activations = code_data.get('activations', 0)
            used = code_data.get('used', 0)
            text += f" - {used}/{activations} использований\n"
    else:
        text += "❌ Нет промокодов.\n"
    
    text += "\n👇 <b>Выберите действие:</b>"
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("➕ Создать", callback_data="promocode_create"),
        InlineKeyboardButton("🗑️ Удалить", callback_data="promocode_delete")
    )
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
    
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    await bot.send_message(callback_query.message.chat.id, text, parse_mode="HTML", reply_markup=keyboard)
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == 'promocode_create')
async def promocode_create_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    await bot.send_message(callback_query.message.chat.id, "✏️ <b>Введите название промокода:</b>", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
    await AdminStates.waiting_promocode_name.set()
    await callback_query.answer()

@dp.message_handler(state=AdminStates.waiting_promocode_name)
async def process_promocode_name(message: types.Message, state: FSMContext):
    if message.text == "🏠 Главное меню":
        await state.finish()
        await message.answer("⚡️ <b>Админ панель успешно активирована</b>", parse_mode="HTML", reply_markup=admin_keyboard())
        return
    
    promocode_name = message.text.strip().upper()
    
    data = load_data()
    if promocode_name in data.get('promocodes', {}):
        await message.answer("❌ Такой промокод уже существует.", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        await state.finish()
        return
    
    await state.update_data(promocode_name=promocode_name)
    
    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        InlineKeyboardButton("🎮 Standoff 2", callback_data="promocode_game_standoff"),
        InlineKeyboardButton("🔳 Roblox", callback_data="promocode_game_roblox"),
        InlineKeyboardButton("⭐️ Tg star", callback_data="promocode_game_tgstar")
    )
    keyboard.add(InlineKeyboardButton("🎮 Все игры", callback_data="promocode_game_all"))
    
    await message.answer("👇 <b>Выберите игру для промокода:</b>", parse_mode="HTML", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith('promocode_game_'), state='*')
async def promocode_game_callback(callback_query: types.CallbackQuery, state: FSMContext):
    game = callback_query.data.split('_')[2]
    
    await state.update_data(promocode_game=game)
    
    currency_names = {'standoff': 'Gold', 'roblox': 'Robux', 'tgstar': 'Stars', 'all': 'валюты'}
    currency = currency_names[game]
    
    await bot.send_message(callback_query.message.chat.id, f"✏️ <b>Введите сумму бонуса в {currency}:</b>", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
    await AdminStates.waiting_promocode_bonus.set()
    await callback_query.answer()

@dp.message_handler(state=AdminStates.waiting_promocode_bonus)
async def process_promocode_bonus(message: types.Message, state: FSMContext):
    if message.text == "🏠 Главное меню":
        await state.finish()
        await message.answer("⚡️ <b>Админ панель успешно активирована</b>", parse_mode="HTML", reply_markup=admin_keyboard())
        return
    
    try:
        bonus = int(message.text)
    except:
        await message.answer("❌ Введите число.", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        return
    
    if bonus <= 0:
        await message.answer("❌ Бонус должен быть > 0.", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        return
    
    await state.update_data(promocode_bonus=bonus)
    await message.answer("✏️ <b>Введите количество активаций (0 = бесконечно):</b>", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
    await AdminStates.waiting_promocode_activations.set()

@dp.message_handler(state=AdminStates.waiting_promocode_activations)
async def process_promocode_activations(message: types.Message, state: FSMContext):
    if message.text == "🏠 Главное меню":
        await state.finish()
        await message.answer("⚡️ <b>Админ панель успешно активирована</b>", parse_mode="HTML", reply_markup=admin_keyboard())
        return
    
    try:
        activations = int(message.text)
    except:
        await message.answer("❌ Введите число.", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        return
    
    if activations < 0:
        await message.answer("❌ Количество не может быть отрицательным.", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        return
    
    state_data = await state.get_data()
    promocode_name = state_data['promocode_name']
    game = state_data['promocode_game']
    bonus = state_data['promocode_bonus']
    
    data = load_data()
    
    if 'promocodes' not in data:
        data['promocodes'] = {}
    
    data['promocodes'][promocode_name] = {
        'game': game,
        'bonus': bonus,
        'activations': activations,
        'used': 0,
        'users': []
    }
    
    save_data(data)
    
    game_names = {'standoff': 'Standoff 2', 'roblox': 'Roblox', 'tgstar': 'TG Star', 'all': 'Все игры'}
    currency = {'standoff': 'Gold', 'roblox': 'Robux', 'tgstar': 'Stars', 'all': 'валюты'}[game]
    
    await message.answer(f"✅ <b>Промокод создан!</b>\n\n🎁 <b>{promocode_name}</b>\n🎮 {game_names[game]}\n💰 {bonus} {currency}\n🔢 Активаций: {activations if activations > 0 else '∞'}", parse_mode="HTML")
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'promocode_delete')
async def promocode_delete_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    await bot.send_message(callback_query.message.chat.id, "✏️ <b>Введите название промокода для удаления:</b>", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
    await AdminStates.waiting_delete_promocode.set()
    await callback_query.answer()

@dp.message_handler(state=AdminStates.waiting_delete_promocode)
async def process_delete_promocode(message: types.Message, state: FSMContext):
    if message.text == "🏠 Главное меню":
        await state.finish()
        await message.answer("⚡️ <b>Админ панель успешно активирована</b>", parse_mode="HTML", reply_markup=admin_keyboard())
        return
    
    promocode_name = message.text.strip().upper()
    data = load_data()
    
    if promocode_name not in data.get('promocodes', {}):
        await message.answer("❌ Такой промокод не существует.", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        await state.finish()
        return
    
    del data['promocodes'][promocode_name]
    save_data(data)
    
    await message.answer(f"✅ <b>Промокод {promocode_name} удален!</b>", parse_mode="HTML")
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'admin_templates')
async def admin_templates_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    templates_data = load_templates()
    templates = templates_data.get('templates', [])
    
    text = "📝 <b>Управление шаблонами ответов</b>\n\n"
    
    if templates:
        categories = {}
        for template in templates:
            category = template.get('category', 'Без категории')
            if category not in categories:
                categories[category] = []
            categories[category].append(template)
        
        for category, category_templates in categories.items():
            text += f"<b>📂 {category}:</b>\n"
            for template in category_templates[:5]:
                text += f"  • {template['name']} (ID: {template['id']})\n"
            if len(category_templates) > 5:
                text += f"  ... и еще {len(category_templates) - 5}\n"
            text += "\n"
    else:
        text += "📭 <i>Шаблонов пока нет. Создайте первый!</i>\n\n"
    
    text += "👇 <b>Выберите действие:</b>"
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("➕ Создать шаблон", callback_data="template_create"),
        InlineKeyboardButton("📋 Список всех", callback_data="template_list")
    )
    keyboard.add(
        InlineKeyboardButton("🔍 Быстрый поиск", callback_data="template_search"),
        InlineKeyboardButton("🗑️ Удалить шаблон", callback_data="template_delete")
    )
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
    
    await bot.edit_message_text(
        text,
        callback_query.message.chat.id,
        callback_query.message.message_id,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == 'template_create')
async def template_create_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        InlineKeyboardButton("🛒 Покупки", callback_data="template_cat_purchase"),
        InlineKeyboardButton("💸 Вывод", callback_data="template_cat_withdraw"),
        InlineKeyboardButton("🔄 Тех.вопросы", callback_data="template_cat_tech")
    )
    keyboard.add(
        InlineKeyboardButton("🎮 Игры", callback_data="template_cat_games"),
        InlineKeyboardButton("💰 Баланс", callback_data="template_cat_balance"),
        InlineKeyboardButton("📝 Другое", callback_data="template_cat_other")
    )
    keyboard.add(
        InlineKeyboardButton("✏️ Своя категория", callback_data="template_cat_custom"),
        InlineKeyboardButton("🔙 Назад", callback_data="admin_templates")
    )
    
    await bot.edit_message_text(
        "📂 <b>Выберите категорию для шаблона:</b>\n\nИли создайте свою категорию",
        callback_query.message.chat.id,
        callback_query.message.message_id,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('template_cat_'))
async def template_category_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    cat_type = callback_query.data.split('_')[2]
    
    categories = {
        'purchase': 'Покупки',
        'withdraw': 'Вывод',
        'tech': 'Технические вопросы',
        'games': 'Игры',
        'balance': 'Баланс',
        'other': 'Другое'
    }
    
    if cat_type == 'custom':
        await bot.edit_message_text(
            "✏️ <b>Введите название своей категории:</b>\n\n<i>Например: Проблемы с оплатой, Вопросы по бонусам и т.д.</i>",
            callback_query.message.chat.id,
            callback_query.message.message_id,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Назад", callback_data="template_create"))
        )
        await AdminStates.waiting_template_category.set()
    else:
        category_name = categories.get(cat_type, 'Другое')
        await dp.current_state(user=callback_query.from_user.id).update_data(template_category=category_name)
        
        await bot.edit_message_text(
            f"📝 <b>Создание шаблона</b>\n📂 <b>Категория:</b> {category_name}\n\n✏️ <b>Введите название шаблона:</b>\n<i>Кратко, что это за ответ. Например: 'Заявка принята', 'Проблема с оплатой'</i>",
            callback_query.message.chat.id,
            callback_query.message.message_id,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Назад", callback_data="template_create"))
        )
        await AdminStates.waiting_template_name.set()
    
    await callback_query.answer()

@dp.message_handler(state=AdminStates.waiting_template_category)
async def process_template_category(message: types.Message, state: FSMContext):
    if message.text == "🏠 Главное меню":
        await state.finish()
        await message.answer("⚡️ <b>Админ панель</b>", parse_mode="HTML", reply_markup=admin_keyboard())
        return
    
    category_name = message.text.strip()
    
    if len(category_name) > 50:
        await message.answer("❌ Слишком длинное название категории (макс. 50 символов).", parse_mode="HTML")
        return
    
    await state.update_data(template_category=category_name)
    
    try:
        await message.delete()
    except:
        pass
    
    await message.answer(
        f"📝 <b>Создание шаблона</b>\n📂 <b>Категория:</b> {category_name}\n\n✏️ <b>Введите название шаблона:</b>\n<i>Кратко, что это за ответ. Например: 'Заявка принята', 'Проблема с оплатой'</i>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Назад", callback_data="template_create"))
    )
    await AdminStates.waiting_template_name.set()

@dp.message_handler(state=AdminStates.waiting_template_name)
async def process_template_name(message: types.Message, state: FSMContext):
    if message.text == "🏠 Главное меню":
        await state.finish()
        await message.answer("⚡️ <b>Админ панель</b>", parse_mode="HTML", reply_markup=admin_keyboard())
        return
    
    template_name = message.text.strip()
    
    if len(template_name) > 100:
        await message.answer("❌ Слишком длинное название (макс. 100 символов).", parse_mode="HTML")
        return
    
    await state.update_data(template_name=template_name)
    
    try:
        await message.delete()
    except:
        pass
    
    await message.answer(
        f"📝 <b>Создание шаблона</b>\n📂 <b>Категория:</b> {(await state.get_data()).get('template_category', 'Без категории')}\n🏷️ <b>Название:</b> {template_name}\n\n✏️ <b>Введите текст шаблона:</b>\n\n<b>Доступные переменные:</b>\n• <code>{{username}}</code> - имя пользователя\n• <code>{{user_id}}</code> - ID пользователя\n• <code>{{amount}}</code> - сумма (если есть)\n• <code>{{game}}</code> - название игры\n• <code>{{date}}</code> - текущая дата\n\n<i>Пример: Привет, {{username}}! Ваша заявка принята.</i>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Назад", callback_data="admin_templates"))
    )
    await AdminStates.waiting_template_text.set()

@dp.message_handler(state=AdminStates.waiting_template_text)
async def process_template_text(message: types.Message, state: FSMContext):
    if message.text == "🏠 Главное меню":
        await state.finish()
        await message.answer("⚡️ <b>Админ панель</b>", parse_mode="HTML", reply_markup=admin_keyboard())
        return
    
    template_text = message.text.strip()
    
    if len(template_text) < 5:
        await message.answer("❌ Текст шаблона слишком короткий (мин. 5 символов).", parse_mode="HTML")
        return
    
    state_data = await state.get_data()
    
    templates_data = load_templates()
    
    new_template = {
        'id': templates_data['next_id'],
        'name': state_data['template_name'],
        'category': state_data.get('template_category', 'Без категории'),
        'text': template_text,
        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'created_by': message.from_user.username or message.from_user.first_name,
        'used_count': 0
    }
    
    templates_data['templates'].append(new_template)
    templates_data['next_id'] += 1
    save_templates(templates_data)
    
    try:
        await message.delete()
    except:
        pass
    
    await message.answer(
        f"✅ <b>Шаблон создан!</b>\n\n📂 <b>Категория:</b> {new_template['category']}\n🏷️ <b>Название:</b> {new_template['name']}\n📝 <b>Текст:</b>\n{template_text[:200]}{'...' if len(template_text) > 200 else ''}\n\n🆔 <b>ID:</b> {new_template['id']}\n📅 <b>Создан:</b> {new_template['created_at']}",
        parse_mode="HTML"
    )
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'template_list')
async def template_list_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    templates_data = load_templates()
    templates = templates_data.get('templates', [])
    
    if not templates:
        await callback_query.answer("📭 Шаблонов пока нет!")
        return
    
    await show_templates_page(callback_query, templates, page=0)
    await callback_query.answer()

async def show_templates_page(callback_query, templates, page=0, items_per_page=5):
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    page_templates = templates[start_idx:end_idx]
    
    total_pages = (len(templates) + items_per_page - 1) // items_per_page
    
    text = f"📋 <b>Все шаблоны</b> (стр. {page + 1}/{total_pages})\n\n"
    
    for i, template in enumerate(page_templates, start=start_idx + 1):
        text += f"<b>{i}. {template['name']}</b> (ID: {template['id']})\n"
        text += f"📂 {template['category']} | 📅 {template['created_at'].split()[0]}\n"
        text += f"👤 {template['created_by']} | 🔢 Использован: {template.get('used_count', 0)} раз\n"
        text += f"📝 {template['text'][:100]}..."
        text += "\n" + "─" * 30 + "\n\n"
    
    keyboard = InlineKeyboardMarkup(row_width=3)
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"templates_page_{page-1}"))
    
    nav_buttons.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="no_action"))
    
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Вперед ➡️", callback_data=f"templates_page_{page+1}"))
    
    if nav_buttons:
        keyboard.row(*nav_buttons)
    
    action_buttons = []
    for template in page_templates:
        action_buttons.append(InlineKeyboardButton(f"✏️ {template['id']}", callback_data=f"template_edit_{template['id']}"))
        action_buttons.append(InlineKeyboardButton(f"🗑️ {template['id']}", callback_data=f"template_delete_{template['id']}"))
        action_buttons.append(InlineKeyboardButton(f"📋 {template['id']}", callback_data=f"template_view_{template['id']}"))
    
    for i in range(0, len(action_buttons), 3):
        keyboard.row(*action_buttons[i:i+3])
    
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_templates"))
    
    await bot.edit_message_text(
        text,
        callback_query.message.chat.id,
        callback_query.message.message_id,
        parse_mode="HTML",
        reply_markup=keyboard
    )

@dp.callback_query_handler(lambda c: c.data.startswith('templates_page_'))
async def templates_page_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    page = int(callback_query.data.split('_')[2])
    templates_data = load_templates()
    templates = templates_data.get('templates', [])
    
    await show_templates_page(callback_query, templates, page)
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('template_view_'))
async def template_view_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    template_id = int(callback_query.data.split('_')[2])
    template = get_template_by_id(template_id)
    
    if not template:
        await callback_query.answer("❌ Шаблон не найден!")
        return
    
    text = f"📋 <b>Шаблон #{template['id']}</b>\n\n"
    text += f"🏷️ <b>Название:</b> {template['name']}\n"
    text += f"📂 <b>Категория:</b> {template['category']}\n"
    text += f"👤 <b>Создал:</b> {template['created_by']}\n"
    text += f"📅 <b>Создан:</b> {template['created_at']}\n"
    text += f"🔢 <b>Использован:</b> {template.get('used_count', 0)} раз\n\n"
    text += f"📝 <b>Текст шаблона:</b>\n"
    text += "─" * 30 + "\n"
    text += f"{template['text']}\n"
    text += "─" * 30 + "\n\n"
    text += "<b>Доступные переменные:</b>\n"
    text += "• <code>{username}</code> - имя пользователя\n"
    text += "• <code>{user_id}</code> - ID пользователя\n"
    text += "• <code>{amount}</code> - сумма\n"
    text += "• <code>{game}</code> - игра\n"
    text += "• <code>{date}</code> - дата\n"
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✏️ Редактировать", callback_data=f"template_edit_{template_id}"),
        InlineKeyboardButton("🗑️ Удалить", callback_data=f"template_delete_{template_id}")
    )
    keyboard.add(
        InlineKeyboardButton("📋 Использовать", callback_data=f"template_use_{template_id}"),
        InlineKeyboardButton("🔙 Назад к списку", callback_data="template_list")
    )
    
    await bot.edit_message_text(
        text,
        callback_query.message.chat.id,
        callback_query.message.message_id,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == 'template_search')
async def template_search_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    await bot.edit_message_text(
        "🔍 <b>Введите текст для поиска шаблона:</b>\n\n<i>Будет произведен поиск по названию и тексту шаблона</i>",
        callback_query.message.chat.id,
        callback_query.message.message_id,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Назад", callback_data="admin_templates"))
    )
    await AdminStates.waiting_user_id.set()
    await dp.current_state(user=callback_query.from_user.id).update_data(action='search_template')
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == 'template_delete')
async def template_delete_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⛔️ Доступ запрещён!")
        return
    
    await bot.edit_message_text(
        "🗑️ <b>Введите ID шаблона для удаления:</b>",
        callback_query.message.chat.id,
        callback_query.message.message_id,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Назад", callback_data="admin_templates"))
    )
    await AdminStates.waiting_user_id.set()
    await dp.current_state(user=callback_query.from_user.id).update_data(action='delete_template')
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == 'activate_promocode')
async def activate_promocode_callback(callback_query: types.CallbackQuery):
    if callback_query.message.chat.id == SUPPORT_GROUP_ID:
        await callback_query.answer()
        return
    
    user_id = str(callback_query.from_user.id)
    data = load_data()
    
    if user_id not in data['users']:
        await callback_query.answer("❌ Пользователь не найден!")
        return
    
    user_data = data['users'][user_id]
    if user_data.get('banned', False):
        await callback_query.answer("🚫 Вы забанены!")
        return
    
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    await bot.send_message(callback_query.message.chat.id, "✏️ <b>Введите промокод:</b>", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
    await UserStates.waiting_promocode.set()
    await callback_query.answer()

@dp.message_handler(state=UserStates.waiting_promocode)
async def process_promocode(message: types.Message, state: FSMContext):
    if message.text == "🏠 Главное меню":
        await state.finish()
        data = load_data()
        user_id = str(message.from_user.id)
        user_data = data['users'].get(user_id, {})
        await show_game_menu(message.chat.id, user_data.get('game', 'standoff'), user_data['username'])
        return
    
    promocode = message.text.strip().upper()
    user_id = str(message.from_user.id)
    data = load_data()
    
    if user_id not in data['users']:
        await message.answer("❌ Пользователь не найден.", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        await state.finish()
        return
    
    if promocode not in data.get('promocodes', {}):
        await message.answer("❌ Промокод не найден.", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        await state.finish()
        return
    
    promocode_data = data['promocodes'][promocode]
    
    if user_id in promocode_data.get('users', []):
        await message.answer("❌ Вы уже активировали этот промокод.", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        await state.finish()
        return
    
    if promocode_data['activations'] > 0 and promocode_data.get('used', 0) >= promocode_data['activations']:
        await message.answer("❌ Лимит активаций промокода исчерпан.", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
        await state.finish()
        return
    
    game = promocode_data['game']
    bonus = promocode_data['bonus']
    
    user_data = data['users'][user_id]
    
    if game == 'all' or game == user_data.get('game'):
        if game == 'all':
            current_game = user_data.get('game', 'standoff')
            if current_game == 'standoff':
                user_data['balance_standoff'] += bonus
                currency = 'Gold'
            elif current_game == 'roblox':
                user_data['balance_roblox'] += bonus
                currency = 'Robux'
            elif current_game == 'tgstar':
                user_data['balance_tgstar'] += bonus
                currency = 'Stars'
        else:
            if game == 'standoff':
                user_data['balance_standoff'] += bonus
                currency = 'Gold'
            elif game == 'roblox':
                user_data['balance_roblox'] += bonus
                currency = 'Robux'
            elif game == 'tgstar':
                user_data['balance_tgstar'] += bonus
                currency = 'Stars'
        
        if 'users' not in promocode_data:
            promocode_data['users'] = []
        promocode_data['users'].append(user_id)
        promocode_data['used'] = promocode_data.get('used', 0) + 1
        
        save_data(data)
        
        game_names = {'standoff': 'Standoff 2', 'roblox': 'Roblox', 'tgstar': 'TG Star', 'all': 'текущей игры'}
        
        await message.answer(f"✅ <b>Промокод активирован!</b>\n\n🎁 <b>{promocode}</b>\n🎮 {game_names[game]}\n💰 +{bonus} {currency}", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
    else:
        game_names = {'standoff': 'Standoff 2', 'roblox': 'Roblox', 'tgstar': 'TG Star'}
        await message.answer(f"❌ Промокод только для {game_names[game]}.", parse_mode="HTML", reply_markup=main_menu_reply_keyboard())
    
    await state.finish()

@dp.message_handler(lambda message: message.text == "🎮 Сменить игру")
async def change_game_button(message: types.Message):
    if message.chat.id == SUPPORT_GROUP_ID:
        return
    
    user_id = str(message.from_user.id)
    data = load_data()
    
    if user_id not in data['users']:
        await message.answer("❌ Пользователь не найден.", parse_mode="HTML")
        return
    
    try:
        await message.delete()
    except:
        pass
    
    await message.answer("👇 Выберите игру:", parse_mode="HTML", reply_markup=games_keyboard())

@dp.message_handler(lambda message: message.text == "⭐️ TG Premium")
async def tg_premium_button(message: types.Message):
    if message.chat.id == SUPPORT_GROUP_ID:
        return
    
    user_id = str(message.from_user.id)
    data = load_data()
    
    if user_id not in data['users']:
        await message.answer("❌ Пользователь не найден.", parse_mode="HTML")
        return
    
    user_data = data['users'][user_id]
    if user_data.get('game') != 'tgstar':
        await message.answer("❌ Функция только для TG Star.", parse_mode="HTML")
        return
    
    try:
        await message.delete()
    except:
        pass
    
    premium_text = "⭐️ <b>Быстрая и удобная покупка TG Premium🔥</b>\n\n"
    premium_text += "<b>Вход в аккаунт🤔</b>\n"
    premium_text += "🎁 1 месяц - 44.990 сум \n"
    premium_text += "🎁 12 месяцев - 329.000 сум\n\n"
    premium_text += "<b>⭐Без входа в аккаунт</b>\n"
    premium_text += "🎁 3 месяца - 189.000 сум \n"
    premium_text += "🎁 6 месяца - 289.000 сум\n"
    premium_text += "🎁 12 месяцев - 429.000 сум\n\n"
    premium_text += "➡️<b>Для покупки TG Premium нажмите кнопку ниже:</b>"
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🛒 Купить", url="https://t.me/kamrush_k"))
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="tg_premium_back"))
    
    await message.answer(premium_text, parse_mode="HTML", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == 'tg_premium_back')
async def tg_premium_back_callback(callback_query: types.CallbackQuery):
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    data = load_data()
    user_id = str(callback_query.from_user.id)
    user_data = data['users'].get(user_id, {})
    await show_game_menu(callback_query.message.chat.id, user_data.get('game', 'standoff'), user_data['username'])
    await callback_query.answer()

@dp.message_handler()
async def unknown_message(message: types.Message):
    if message.chat.id == SUPPORT_GROUP_ID:
        try:
            await message.delete()
        except:
            pass
        return
    
    user_id = str(message.from_user.id)
    data = load_data()
    
    if user_id in data['users']:
        user_data = data['users'][user_id]
        if user_data.get('banned', False):
            await message.answer("🚫 <b>Вы забанены.</b>", parse_mode="HTML")
            return

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
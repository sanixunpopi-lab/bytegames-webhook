import asyncio
import logging
import os
import json
import threading
from flask import Flask, request, jsonify
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import Command

# =============================================
# ===== НАСТРОЙКИ =====
# =============================================
BOT_TOKEN = "8996281069:AAH14ZsKMJrr8_ap6JgTJbD5HmKNg5v4KMc"  # НОВЫЙ ТОКЕН
WEBAPP_URL = "https://sanixunpopi-lab.github.io/bytegames-casino/"
ADMIN_ID = 8698280423
ADMIN_USERNAME = "boardrd"

# Для Webhook (Bytecoin)
WEBHOOK_SECRET = "whsec_7HpCA7OJfbQDBiX5MD4anPq_cnvvtuCs33oF4SQjh1c"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# =============================================
# ===== ВРЕМЕННАЯ БАЗА ДАННЫХ (В ПАМЯТИ) =====
# =============================================
user_balances = {}

def get_balance(user_id):
    return user_balances.get(user_id, {}).get('balance', 0)

def add_balance(user_id, amount):
    if user_id not in user_balances:
        user_balances[user_id] = {'balance': 0}
    user_balances[user_id]['balance'] += amount
    return user_balances[user_id]['balance']

# =============================================
# ===== FLASK WEBHOOK СЕРВЕР =====
# =============================================
app = Flask(__name__)

@app.route('/webhook/bytecoin', methods=['POST'])
def bytecoin_webhook():
    """Принимает уведомление от Bytecoin о платеже"""
    try:
        data = request.get_json()
        logging.info(f"📩 Получен Webhook: {data}")

        user_id = data.get('user_id') or data.get('userId') or data.get('user')
        amount = data.get('amount') or data.get('total_amount') or data.get('value')
        
        if not user_id or not amount:
            logging.warning("⚠️ Не найдены user_id или amount в запросе")
            return jsonify({"status": "error", "message": "Missing user_id or amount"}), 400

        user_id = int(user_id)
        amount = float(amount)

        new_balance = add_balance(user_id, amount)
        logging.info(f"✅ Зачислено {amount} BCN пользователю {user_id}. Новый баланс: {new_balance}")

        return jsonify({"status": "success", "balance": new_balance}), 200

    except Exception as e:
        logging.error(f"❌ Ошибка обработки Webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/webhook/bytecoin', methods=['GET'])
def webhook_check():
    """Проверка работоспособности Webhook"""
    return jsonify({"status": "ok", "message": "Webhook is alive"}), 200

@app.route('/')
def index():
    return jsonify({"status": "ok", "message": "ByteGames Bot is running"}), 200

# =============================================
# ===== КОМАНДЫ TELEGRAM БОТА =====
# =============================================
@dp.message(Command("start"))
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎰 Играть в ByteGames",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )],
        [InlineKeyboardButton(
            text="📢 Наш канал",
            url="https://t.me/bytecasinos"
        )],
        [InlineKeyboardButton(
            text="💬 Поддержка",
            url="https://t.me/boardrd"
        )]
    ])
    
    await message.answer(
        "🎮 *ByteGames Casino*\n\n"
        "🚀 Играй в Crash с реальными ставками\n"
        "💰 Пополнение через Bytecoin — автоматически!\n"
        "👥 Приводи друзей и получай 3% от их проигрышей\n"
        "🎫 Активируй промокоды и получай бонусы\n\n"
        "⬇️ Нажми кнопку ниже, чтобы начать!",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@dp.message(Command("balance"))
async def balance(message: types.Message):
    user_id = message.from_user.id
    bal = get_balance(user_id)
    await message.answer(
        f"📊 *Ваш баланс*\n\n"
        f"💰 Основной: {bal:.2f} BCN\n"
        f"🎁 Бонусный: 0.00 BCN",
        parse_mode="Markdown"
    )

@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    await message.answer(
        "❓ *Помощь*\n\n"
        "🎮 Играть — нажми кнопку 'Играть в ByteGames'\n"
        "💰 Пополнить — в приложении выбери 'Пополнить'\n"
        "💸 Вывести — в приложении выбери 'Вывести'\n"
        "👥 Рефералы — приведи друга и получай 3%\n"
        "🎫 Промокоды — активируй в приложении\n\n"
        "По всем вопросам: @boardrd",
        parse_mode="Markdown"
    )

# =============================================
# ===== ЗАПУСК =====
# =============================================
def run_flask():
    """Запускает Flask сервер в отдельном потоке"""
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

async def main():
    # Жесткий сброс вебхука — УБИВАЕТ КОНФЛИКТЫ
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(url="")  # Очищаем вебхук
    
    # Запускаем Flask в фоновом потоке
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logging.info(f"🚀 Flask сервер для Webhook запущен на порту {os.environ.get('PORT', 10000)}")

    # Запускаем Telegram бота
    logging.info("🤖 Telegram бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

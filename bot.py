import asyncio
import logging
import os
import re
import threading
from flask import Flask, request, jsonify
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import Command

# =============================================
# ===== НАСТРОЙКИ =====
# =============================================
BOT_TOKEN = "8996281069:AAH14ZsKMJrr8_ap6JgTJbD5HmKNg5v4KMc"
WEBAPP_URL = "https://sanixunpopi-lab.github.io/bytegames-casino/"
ADMIN_ID = 8698280423
ADMIN_USERNAME = "boardrd"
WEBHOOK_SECRET = "whsec_7HpCA7OJfbQDBiX5MD4anPq_cnvvtuCs33oF4SQjh1c"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# =============================================
# ===== ВРЕМЕННАЯ БАЗА (В ПАМЯТИ) =====
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
    """Универсальный приём Webhook от Bytecoin"""
    try:
        # 1. Получаем данные во всех возможных форматах
        data = request.get_json(silent=True)
        if not data:
            data = request.form.to_dict() or {}
        logging.info(f"📩 ПОЛНЫЙ ЗАПРОС ОТ BYTECOIN: {data}")

        # 2. Ищем user_id во ВСЕХ возможных полях, включая комментарий
        user_id = None
        possible_fields = [
            'user_id', 'userId', 'user', 'tg_id', 'telegram_id',
            'client_id', 'order_id', 'comment', 'payload',
            'description', 'memo', 'label', 'custom_data'
        ]
        for key in possible_fields:
            if key in data and data[key]:
                val = str(data[key])
                # Извлекаем все цифры из значения (для случая, если ID в тексте)
                digits = re.findall(r'\d{5,}', val)
                if digits:
                    user_id = digits[0]
                    logging.info(f"✅ Найден user_id в поле '{key}': {user_id}")
                    break

        # 3. Ищем amount во всех возможных полях
        amount = None
        amount_fields = [
            'amount', 'total_amount', 'value', 'sum',
            'payment_amount', 'merchant_amount',
            'received_amount', 'coin_amount', 'total'
        ]
        for key in amount_fields:
            if key in data and data[key]:
                try:
                    amount = float(str(data[key]).replace(',', '.'))
                    logging.info(f"✅ Найдена сумма в поле '{key}': {amount}")
                    break
                except:
                    pass

        # 4. Если данных нет — отвечаем 200, чтобы Bytecoin не повторял
        if not user_id or not amount:
            logging.warning(f"⚠️ Не найдены user_id или amount. Данные: {data}")
            return jsonify({"status": "ok"}), 200

        # 5. Зачисляем
        user_id = int(user_id)
        new_balance = add_balance(user_id, amount)
        logging.info(f"✅ ЗАЧИСЛЕНО {amount} BCN пользователю {user_id}. Новый баланс: {new_balance}")

        return jsonify({"status": "success", "balance": new_balance}), 200

    except Exception as e:
        logging.error(f"❌ Ошибка обработки Webhook: {e}")
        return jsonify({"status": "ok"}), 200


@app.route('/webhook/bytecoin', methods=['GET'])
def webhook_check():
    """Проверка работоспособности Webhook"""
    return jsonify({"status": "ok", "message": "Webhook is alive"}), 200


@app.route('/')
def index():
    return jsonify({"status": "ok", "message": "ByteGames Bot is running"}), 200


# =============================================
# ===== КОМАНДЫ БОТА =====
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
        "🎫 Промокоды — активируй в приложении",
        parse_mode="Markdown"
    )


@dp.message(Command("myid"))
async def my_id(message: types.Message):
    """Показывает ID пользователя — нужен для комментария к переводу"""
    await message.answer(
        f"🆔 Ваш Telegram ID:\n`{message.from_user.id}`\n\n"
        f"⚠️ Укажите этот ID в комментарии к переводу в Bytecoin!",
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
    # Сброс вебхука (убивает конфликты)
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(url="")

    # Запуск Flask в фоне
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logging.info(f"🚀 Flask запущен на порту {os.environ.get('PORT', 10000)}")

    # Запуск бота
    logging.info("🤖 Telegram бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import logging
import os
import re
import time
import threading
import aiohttp
from flask import Flask, request, jsonify
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import Command

# =============================================
# ===== НАСТРОЙКИ =====
# =============================================
BOT_TOKEN = "8996281069:AAHHAyq0OMdLXXreownMoVuGkVISnQn14gI"
WEBAPP_URL = "https://sanixunpopi-lab.github.io/bytegames-casino/"
ADMIN_ID = 8698280423
ADMIN_USERNAME = "boardrd"
WEBHOOK_SECRET = "whsec_7HpCA7OJfbQDBiX5MD4anPq_cnvvtuCs33oF4SQjh1c"

# ===== BYTECOIN API =====
BYTECOIN_API_KEY = "bc_live_ZL_wrwnBohl--hIbC6uRm6IdRCZcHBF1sWT664-0r9A"
BYTECOIN_API_URL = "https://api.bytecoin.com/v1/invoice/create"
BYTECOIN_WEBHOOK_URL = "https://bytegames-webhook-1.onrender.com/webhook/bytecoin"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# =============================================
# ===== ВРЕМЕННАЯ БАЗА =====
# =============================================
user_balances = {}
pending_invoices = {}

def get_balance(user_id):
    return user_balances.get(user_id, {}).get('balance', 0)

def add_balance(user_id, amount):
    if user_id not in user_balances:
        user_balances[user_id] = {'balance': 0}
    user_balances[user_id]['balance'] += amount
    return user_balances[user_id]['balance']

# =============================================
# ===== СОЗДАНИЕ СЧЁТА =====
# =============================================
async def create_bytecoin_invoice(user_id, amount):
    order_id = f"user_{user_id}_{int(time.time())}"

    headers = {
        "Authorization": f"Bearer {BYTECOIN_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "amount": str(amount),
        "currency": "BYTECOIN",
        "order_id": order_id,
        "url_callback": BYTECOIN_WEBHOOK_URL,
        "payload": str(user_id),
        "description": f"Пополнение баланса игрока {user_id}"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(BYTECOIN_API_URL, json=payload, headers=headers) as resp:
                data = await resp.json()
                logging.info(f"📤 Ответ Bytecoin API: {data}")

                if resp.status == 200:
                    invoice_url = (
                        data.get("url") or
                        data.get("result", {}).get("url") or
                        data.get("payment_url")
                    )
                    invoice_id = (
                        data.get("uuid") or
                        data.get("result", {}).get("uuid") or
                        data.get("invoice_id")
                    )

                    if invoice_id:
                        pending_invoices[invoice_id] = user_id

                    return invoice_url
                else:
                    logging.error(f"❌ Ошибка создания счёта: {data}")
                    return None
    except Exception as e:
        logging.error(f"❌ Ошибка API: {e}")
        return None

# =============================================
# ===== FLASK WEBHOOK (ИСПРАВЛЕНО!) =====
# =============================================
app = Flask(__name__)

@app.route('/webhook/bytecoin', methods=['POST'])
def bytecoin_webhook():
    try:
        raw = request.get_json(silent=True) or request.form.to_dict() or {}
        logging.info(f"📩 WEBHOOK ОТ BYTECOIN: {raw}")

        # ===== ДАННЫЕ ВСЕГДА ВНУТРИ 'data' =====
        data = raw.get('data', raw)
        event = raw.get('event', '')

        # Проверяем что это входящий перевод
        if event and event != 'transfer.received':
            logging.info(f"ℹ️ Игнорируем событие: {event}")
            return jsonify({"status": "ok"}), 200

        # ===== БЕРЁМ USER_ID (это ID отправителя) =====
        user_id = data.get('user_id')
        amount_raw = data.get('sum')
        side = data.get('side')

        # Проверяем что перевод на сервис
        if side and side != 'to_service':
            logging.info(f"ℹ️ Игнорируем перевод: side={side}")
            return jsonify({"status": "ok"}), 200

        if not user_id or not amount_raw:
            logging.warning(f"⚠️ Нет user_id или sum. Данные: {data}")
            return jsonify({"status": "ok"}), 200

        # ===== ПРЕОБРАЗУЕМ =====
        user_id = int(user_id)
        amount = float(str(amount_raw).replace(',', '.'))

        # ===== ЗАЧИСЛЯЕМ =====
        new_balance = add_balance(user_id, amount)
        logging.info(f"✅ ЗАЧИСЛЕНО {amount} BCN игроку {user_id}. Баланс: {new_balance}")

        return jsonify({"status": "success", "balance": new_balance}), 200

    except Exception as e:
        logging.error(f"❌ Ошибка обработки Webhook: {e}")
        return jsonify({"status": "ok"}), 200


@app.route('/webhook/bytecoin', methods=['GET'])
def webhook_check():
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
        [InlineKeyboardButton(text="🎰 Играть в ByteGames", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton(text="📢 Наш канал", url="https://t.me/bytecasinos")],
        [InlineKeyboardButton(text="💬 Поддержка", url="https://t.me/boardrd")]
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
        f"📊 *Ваш баланс*\n\n💰 Основной: {bal:.2f} BCN\n🎁 Бонусный: 0.00 BCN",
        parse_mode="Markdown"
    )

@dp.message(Command("deposit"))
async def deposit_cmd(message: types.Message):
    await message.answer("💰 Введите сумму пополнения (мин 10 BCN):")

@dp.message(lambda m: m.text and m.text.isdigit())
async def process_deposit_amount(message: types.Message):
    user_id = message.from_user.id
    amount = int(message.text)

    if amount < 10:
        await message.answer("❌ Минимальная сумма — 10 BCN")
        return

    await message.answer("⏳ Создаём счёт...")
    invoice_url = await create_bytecoin_invoice(user_id, amount)

    if invoice_url:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить", url=invoice_url)]
        ])
        await message.answer(
            f"✅ Счёт на {amount} BCN создан!\n\nНажми кнопку ниже для оплаты:",
            reply_markup=keyboard
        )
    else:
        await message.answer("❌ Не удалось создать счёт. Попробуй позже или напиши @boardrd")

@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    await message.answer(
        "❓ *Помощь*\n\n"
        "🎮 Играть — нажми 'Играть в ByteGames'\n"
        "💰 Пополнить — команда /deposit\n"
        "💸 Вывести — в приложении 'Вывести'\n"
        "👥 Рефералы — приведи друга и получай 3%\n"
        "🎫 Промокоды — активируй в приложении",
        parse_mode="Markdown"
    )

# =============================================
# ===== ЗАПУСК =====
# =============================================
def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

async def main():
    logging.info("🧹 Сбрасываем старые сессии Telegram...")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await bot.set_webhook(url="")
        await asyncio.sleep(3)
        logging.info("✅ Старые сессии сброшены")
    except Exception as e:
        logging.warning(f"⚠️ Ошибка сброса: {e}")

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logging.info(f"🚀 Flask запущен на порту {os.environ.get('PORT', 10000)}")

    logging.info("🤖 Telegram бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

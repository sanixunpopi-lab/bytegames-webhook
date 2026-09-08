import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import Command

# ===== НАСТРОЙКИ =====
BOT_TOKEN = "8996281069:AAFekiIx20ojqZpWBcvbEGryoytp5c1-0IM"  # Твой токен
WEBAPP_URL = "https://sanixunpopi-lab.github.io/bytegames-casino/"
ADMIN_ID = 8698280423
ADMIN_USERNAME = "boardrd"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ===== КОМАНДА /START =====
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
        "💰 Пополнение через @boardrd\n"
        "👥 Приводи друзей и получай 3% от их проигрышей\n"
        "🎫 Активируй промокоды и получай бонусы\n\n"
        "⬇️ Нажми кнопку ниже, чтобы начать!",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@dp.message(Command("balance"))
async def balance(message: types.Message):
    await message.answer("📊 Ваш баланс: 0.00 BCN\n💎 Бонусный: 0.00 BCN")

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

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    print("🤖 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
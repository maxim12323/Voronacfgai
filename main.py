import logging
import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from openai import OpenAI
from aiohttp import web

# --- НАСТРОЙКИ ---
# Рекомендуется вставить токены сюда, если не используешь Environment Variables
TELEGRAM_TOKEN = "8539550683:AAFlcuC4UCWWS3A_d3x_wLz85-2x0T_4lr4"
SAMBANOVA_API_KEY = "2d2954e5-1b83-443e-96ec-df7bb9ac8613"
KNOWLEDGE_BASE_PATH = "instruction.txt"

# Инициализация ИИ (SambaNova)
client = OpenAI(
    api_key=SAMBANOVA_API_KEY, 
    base_url="https://api.sambanova.ai/v1"
)

# Инициализация бота
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# --- БЛОК ДЛЯ KOYEB (WEB SERVER) ---
async def handle_health_check(request):
    return web.Response(text="Bot is running!", status=200)

async def start_koyeb_helper():
    app = web.Application()
    app.router.add_get('/', handle_health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    # Koyeb по умолчанию ищет порт 8000
    site = web.TCPSite(runner, '0.0.0.0', 8000)
    await site.start()
    logging.info("Koyeb health check server started on port 8000")

# --- ЛОГИКА БОТА ---
def get_knowledge_base():
    try:
        if os.path.exists(KNOWLEDGE_BASE_PATH):
            with open(KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as f:
                return f.read()
        return "Инструкция временно недоступна."
    except Exception as e:
        return f"Ошибка чтения файла: {e}"

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Бот успешно запущен в облаке и готов к работе!")

@dp.message()
async def handle_message(message: types.Message):
    kb_content = get_knowledge_base()
    try:
        response = client.chat.completions.create(
            model="Meta-Llama-3.1-8B-Instruct",
            messages=[
                {
                    "role": "system", 
                    "content": f"Ты помощник. Отвечай только на основе этого текста: {kb_content}. Если ответа нет, скажи, что не знаешь."
                },
                {"role": "user", "content": message.text}
            ]
        )
        await message.answer(response.choices[0].message.content)
    except Exception as e:
        logging.error(f"Ошибка ИИ: {e}")
        await message.answer("Произошла ошибка при обработке запроса.")

# --- ЗАПУСК ---
async def main():
    logging.basicConfig(level=logging.INFO)
    
    # Запускаем "обманку" для Koyeb
    await start_koyeb_helper()
    
    # Запускаем бота
    print("Бот запущен 24/7...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен")
        
import logging
import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.chat_action import ChatActionSender
from openai import AsyncOpenAI  # Заменено на асинхронный клиент
from aiohttp import web

# --- НАСТРОЙКИ ---
TELEGRAM_TOKEN = "8125676444:AAHoGTJlsr7OBtp-BFg50L4h7m8XJyn2UCY"
SAMBANOVA_API_KEY = "2d2954e5-1b83-443e-96ec-df7bb9ac8613"
KNOWLEDGE_BASE_PATH = "instruction.txt"

# Инициализация асинхронного клиента ИИ (SambaNova)
client = AsyncOpenAI(
    api_key=SAMBANOVA_API_KEY, 
    base_url="https://api.sambanova.ai/v1"
)

# Инициализация бота
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# --- БЛОК ДЛЯ СТАБИЛЬНОЙ РАБОТЫ (HEALTH CHECK) ---
async def handle_health_check(request):
    return web.Response(text="Bot is running!", status=200)

async def start_koyeb_helper():
    app = web.Application()
    app.router.add_get('/', handle_health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8000)
    await site.start()
    logging.info("Health check server started on port 8000")

# --- ЛОГИКА БАЗЫ ЗНАНИЙ ---
def get_knowledge_base():
    try:
        if os.path.exists(KNOWLEDGE_BASE_PATH):
            with open(KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as f:
                content = f.read().strip()
                return content if content else "Инструкция пуста."
        return "Файл инструкции не найден."
    except Exception as e:
        return f"Ошибка чтения файла: {e}"

# --- ОБРАБОТЧИКИ КОМАНД ---
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Бот успешно запущен и готов к работе! Задавайте вопросы по инструкции.")

# --- ОСНОВНОЙ ОБРАБОТЧИК ---
@dp.message()
async def handle_message(message: types.Message):
    if not message.text:
        return

    kb_content = get_knowledge_base()

    # Показываем статус "печатает", пока ждем ответ от SambaNova
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        try:
            # Асинхронный запрос к нейросети
            response = await client.chat.completions.create(
                model="Meta-Llama-3.1-8B-Instruct",
                messages=[
                    {
                        "role": "system", 
                        "content": f"Ты строгий помощник. Отвечай ТОЛЬКО на основе этого текста: {kb_content}. Если ответа в тексте нет, вежливо скажи, что не знаешь."
                    },
                    {"role": "user", "content": message.text}
                ],
                temperature=0.7
            )
            
            answer = response.choices[0].message.content
            await message.answer(answer)
            
        except Exception as e:
            logging.error(f"Ошибка ИИ: {e}")
            # Отправляем краткое описание ошибки в чат для отладки
            await message.answer(f"⚠️ Ошибка при запросе к ИИ. Проверьте логи сервера.")

# --- ЗАПУСК ---
async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    # Запуск веб-сервера (для Koyeb/Bothost)
    await start_koyeb_helper()
    
    logging.info("Бот запускается...")
    # Удаляем вебхуки перед запуском polling, чтобы не было конфликтов
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен")
        

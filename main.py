import logging
import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.chat_action import ChatActionSender  # Добавлено для эффекта "печатает"
from openai import OpenAI
from aiohttp import web

# --- НАСТРОЙКИ ---
TELEGRAM_TOKEN = "8125676444:AAHoGTJlsr7OBtp-BFg50L4h7m8XJyn2UCY"
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

# --- БЛОК ДЛЯ СТАБИЛЬНОЙ РАБОТЫ (HEALTH CHECK) ---
async def handle_health_check(request):
    return web.Response(text="Bot is running!", status=200)

async def start_koyeb_helper():
    app = web.Application()
    app.router.add_get('/', handle_health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    # Порт 8000 для совместимости с облачными сервисами
    site = web.TCPSite(runner, '0.0.0.0', 8000)
    await site.start()
    logging.info("Health check server started on port 8000")

# --- ЛОГИКА БАЗЫ ЗНАНИЙ ---
def get_knowledge_base():
    try:
        if os.path.exists(KNOWLEDGE_BASE_PATH):
            with open(KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as f:
                return f.read()
        return "Инструкция временно недоступна."
    except Exception as e:
        return f"Ошибка чтения файла: {e}"

# --- ОБРАБОТЧИКИ КОМАНД ---
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Бот успешно запущен и готов к работе! Задавайте ваши вопросы.")

# --- ОСНОВНОЙ ОБРАБОТЧИК С ЭФФЕКТОМ "ПЕЧАТАЕТ" ---
@dp.message()
async def handle_message(message: types.Message):
    # Если сообщения нет (например, пришел стикер), выходим
    if not message.text:
        return

    kb_content = get_knowledge_base()

    # Включаем статус "печатает..." на время запроса к ИИ
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        try:
            # Запрос к нейросети (синхронный вызов в асинхронном методе)
            # Если бот будет "зависать", можно обернуть в run_in_executor
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
            
            answer = response.choices[0].message.content
            await message.answer(answer)
            
        except Exception as e:
            logging.error(f"Ошибка ИИ: {e}")
            await message.answer("Извините, произошла ошибка при обработке вашего запроса.")

# --- ЗАПУСК БОТА ---
async def main():
    # Настройка логов
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    # Запускаем фоновый веб-сервер
    await start_koyeb_helper()
    
    # Запускаем бесконечный цикл опроса (Polling)
    logging.info("Бот запущен и работает 24/7...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен вручную")
        

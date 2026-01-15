import logging
import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.chat_action import ChatActionSender
from gigachat import GigaChat 
from aiohttp import web

# --- НАСТРОЙКИ ---
TELEGRAM_TOKEN = "8125676444:AAHoGTJlsr7OBtp-BFg50L4h7m8XJyn2UCY"
# Вставь сюда свой длинный ключ Authorization key (Base64)
GIGACHAT_CREDENTIALS = "MDE5YmMxY2YtZmNhMy03ZGZmLWFkZTctZjMwMzUzYjllYzg5OjVkODMxNGRiLTgyMDktNGIyNS04ZTJlLWFlNjg0ZmNmMThmMQ==" 
KNOWLEDGE_BASE_PATH = "instruction.txt"

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# --- ВСПОМОГАТЕЛЬНЫЙ СЕРВЕР ---
async def handle_health_check(request):
    return web.Response(text="Штаб VoronaAi в полной боевой готовности! 🪂", status=200)

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8000)
    await site.start()

# --- ЧТЕНИЕ БАЗЫ ЗНАНИЙ ---
def get_knowledge_base():
    try:
        if os.path.exists(KNOWLEDGE_BASE_PATH):
            with open(KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as f:
                content = f.read().strip()
                return content if content else "Инструкция пуста."
        return "Файл тактических указаний не найден."
    except Exception as e:
        return f"Ошибка связи с архивом: {e}"

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "Приветствую, боец! 🫡\n\n"
        "Я - нейросеть от @voronacfg. Могу помочь скачать тебе любой софт, кфг! Отвечу на любые вопросы и просто могу поднять настроение!🍗"
    )

@dp.message()
async def handle_message(message: types.Message):
    if not message.text:
        return

    kb_content = get_knowledge_base()

    # Анимация "печатает..." для живого общения
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        try:
            # Подключаемся к GigaChat (scope для физлиц)
            with GigaChat(credentials=GIGACHAT_CREDENTIALS, verify_ssl_certs=False, scope='GIGACHAT_API_PERS') as giga:
                response = giga.chat({
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "Ты — самый вежливый, добрый и при этом профессиональный тактический ассистент по установке софтов и читов для PUBG Mobile. "
                                "Твой стиль: дружелюбный напарник, советчик (бро), который всегда готов помочь и подробно подсказать. "
                                "Используй геймерский сленг (лут, зона, катка, дроп, фраги), но оставайся воспитанным. "
                                f"Твои главные данные: {kb_content}. "
                                "ПРАВИЛА ИГРЫ: "
                                "1. Если ответ есть в базе знаний — выдавай его максимально понятно и вежливо. "
                                "2. Если в базе ответа нет — не бросай бойца! Используй свои знания о PUBG Mobile, "
                                "чтобы дать крутой тактический совет или просто поддержать беседу. "
                                "Добавляй эмодзи (🔫, 🎒, 🚁, 🍗, 🔥) и старайся поднять настроение пользователю!"
                                "После каждого своего ответа спрашивай пользователя: всё понятно? Может ещё что то объяснить?"
                            )
                        },
                        {"role": "user", "content": message.text}
                    ],
                    "temperature": 0.8 # Чтобы ответы были живыми и разными
                })
                
                answer = response.choices[0].message.content
                await message.answer(answer)

        except Exception as e:
            logging.error(f"GigaChat Error: {e}")
            await message.answer("Ой, боец, кажется рация барахлит! 📡 Попробуй отправить запрос еще раз, я обязательно отвечу!")

# --- ЗАПУСК ---
async def main():
    logging.basicConfig(level=logging.INFO)
    await start_web_server()
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Бот-читер запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен")

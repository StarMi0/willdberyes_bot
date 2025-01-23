import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from routers import router as main_router
from settings import API_TOKEN

# Логирование
logging.basicConfig(level=logging.INFO)

async def main():
    """
    Основной запуск бота.
    """
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()
    dp.include_router(main_router)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Выход из программы.")

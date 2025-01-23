import requests
from aiogram.client.session import aiohttp
from aiogram.filters import BaseFilter, Command
from aiogram import Router, types, Bot, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from settings import API_URL, BEARER_TOKEN

router = Router(name=__name__)
scheduler = AsyncIOScheduler()  # Инициализация планировщика
active_tasks = {}  # Словарь для отслеживания активных подписок


# Функция для получения данных из API
async def fetch_product_data(bot: Bot, chat_id: int, artikul: str):
    headers = {
        'Authorization': f'Bearer {BEARER_TOKEN}',  # Используем Bearer токен
        'Content-Type': 'application/json'
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{API_URL}/api/v1/products", json={"artikul": int(artikul)}, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    product_name = data.get("name", "Нет названия")
                    product_price = data.get("price", "Не указана")
                    product_rating = data.get("rating", "Не указан")
                    product_stock = data.get("stock", "Не указано")

                    # Формируем сообщение с обновленными данными
                    text = (
                        f"Обновленные данные товара:\n\n"
                        f"Название: {product_name}\n"
                        f"Артикул: {artikul}\n"
                        f"Цена: {product_price}₽\n"
                        f"Рейтинг: {product_rating}\n"
                        f"Остаток: {product_stock} шт."
                    )

                    # Кнопка для отмены подписки
                    unsubscribe_button = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="Отказаться от подписки", callback_data=f"unsubscribe_{artikul}")]
                    ])

                    await bot.send_message(chat_id, text, reply_markup=unsubscribe_button)
                else:
                    await bot.send_message(chat_id, "Ошибка при обновлении данных.")
    except Exception as e:
        await bot.send_message(chat_id, f"Произошла ошибка при обновлении данных: {str(e)}")


@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer("Привет! Введите артикул товара Wildberries для получения информации.")


# Обработчик артикула
@router.message(F.text.regexp(r"^\d+$"))
async def handle_artikul(message: types.Message, bot: Bot, state: FSMContext):
    artikul = message.text.strip()
    headers = {
        'Authorization': f'Bearer {BEARER_TOKEN}',  # Используем Bearer токен
        'Content-Type': 'application/json'
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{API_URL}/api/v1/products", json={"artikul": int(artikul)}, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    product_name = data.get("name", "Нет названия")
                    product_price = data.get("price", "Не указана")
                    product_rating = data.get("rating", "Не указан")
                    product_stock = data.get("stock", "Не указано")

                    # Формируем ответ с характеристиками товара
                    text = (
                        f"Характеристики товара:\n\n"
                        f"Название: {product_name}\n"
                        f"Артикул: {artikul}\n"
                        f"Цена: {product_price}₽\n"
                        f"Рейтинг: {product_rating}\n"
                        f"Остаток: {product_stock} шт."
                    )

                    # Кнопка для подписки
                    subscribe_button = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="Подписаться", callback_data=f"subscribe_{artikul}")]
                    ])

                    await message.answer(text, reply_markup=subscribe_button)
                    await state.clear()
                else:
                    error_message = await response.json()
                    await message.answer(f"Ошибка: {error_message.get('detail', 'Неизвестная ошибка')}")
    except ValueError:
        await message.answer("Артикул должен быть числом. Попробуйте снова.")
    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}")


# Обработчик инлайн-кнопки «Подписаться»
@router.callback_query(F.data.startswith("subscribe_"))
async def handle_subscription(callback: types.CallbackQuery, bot: Bot):
    artikul = callback.data.split("_")[1]
    chat_id = callback.message.chat.id

    # Проверяем, есть ли уже активная подписка
    if artikul in active_tasks:
        await callback.message.answer("Вы уже подписаны на обновление данных по этому артикулу.")
        return

    # Добавляем задачу в планировщик
    scheduler.add_job(fetch_product_data, "interval", minutes=30, args=[bot, chat_id, artikul], id=artikul)
    active_tasks[artikul] = chat_id

    await callback.message.answer(f"Вы подписались на обновление данных по артикулу {artikul}. Обновление каждые 30 минут.")


# Обработчик инлайн-кнопки «Отказаться от подписки»
@router.callback_query(F.data.startswith("unsubscribe_"))
async def handle_unsubscribe(callback: types.CallbackQuery):
    artikul = callback.data.split("_")[1]

    # Проверяем, есть ли активная подписка
    if artikul in active_tasks:
        scheduler.remove_job(artikul)
        del active_tasks[artikul]
        await callback.message.answer(f"Вы отказались от подписки на артикул {artikul}.")
    else:
        await callback.message.answer("Подписка на данный артикул не найдена.")

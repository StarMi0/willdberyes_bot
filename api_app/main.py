import aiohttp
from fastapi import FastAPI, Depends, HTTPException
import requests
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager

from db.requests import add_product, get_product_by_artikul
from func.auth import verify_token
from db.model import AsyncSessionLocal, init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Initializing database...")
    await init_db()
    print("Database initialized successfully!")
    yield
    print("Shutting down application...")

# Инициализация приложения FastAPI
app = FastAPI(lifespan=lifespan)

# Валидатор для POST запроса
class ProductRequest(BaseModel):
    artikul: int = Field(..., gt=0, description="Артикул товара Wildberries")

# Зависимость для получения сессии
async def get_db_session():
    async with AsyncSessionLocal() as session:
        yield session

# Асинхронный сбор данных из Wildberries API
async def fetch_and_store_product(artikul: int, db_session: AsyncSession):
    url = f"https://card.wb.ru/cards/v1/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={artikul}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        product_data = data["data"]["products"][0]  # Предполагаем, что структура данных фиксирована
        await add_product(
            db_session,
            artikul=artikul,
            name=product_data["name"],
            price=product_data["salePriceU"] / 100,
            rating=product_data.get("rating", 0.0),
            stock=product_data.get("quantity", 0),
        )
    else:
        raise HTTPException(status_code=404, detail="Product not found on Wildberries")


# Эндпоинт для POST /api/v1/products
@app.post("/api/v1/products", dependencies=[Depends(verify_token)])
async def create_or_update_product(
    product_request: ProductRequest,
    db_session: AsyncSession = Depends(get_db_session),
):
    artikul = product_request.artikul

    # Пытаемся получить данные из Wildberries
    try:
        url = f"https://card.wb.ru/cards/v1/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={artikul}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=404, detail="Product not found on Wildberries"
                    )

                data = await response.json()
                product_data = data["data"]["products"][0]  # Извлекаем данные о продукте

                # Собираем информацию о товаре
                name = product_data["name"]
                price = product_data["salePriceU"] / 100
                rating = product_data.get("rating", 0.0)
                stock = product_data.get("quantity", 0)

                # Обновляем или создаем запись в БД
                existing_product = await get_product_by_artikul(db_session, artikul)
                if existing_product:
                    # Обновляем данные существующего продукта
                    existing_product.name = name
                    existing_product.price = price
                    existing_product.rating = rating
                    existing_product.stock = stock
                    await db_session.commit()
                else:
                    # Добавляем новый продукт в БД
                    await add_product(
                        db_session, artikul=artikul, name=name, price=price, rating=rating, stock=stock
                    )

                # Формируем ответ с данными товара
                return {
                    "artikul": artikul,
                    "name": name,
                    "price": price,
                    "rating": rating,
                    "stock": stock,
                }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch or store product data: {str(e)}")


# Инициализация базы данных перед запуском приложения
@app.on_event("startup")
async def on_startup():
    print("Initializing database...")
    await init_db()
    print("Database initialized successfully!")


if __name__ == "__main__":
    import asyncio
    import uvicorn

    # Опциональный запуск через asyncio
    asyncio.run(uvicorn.run("main:app", host="127.0.0.1", port=8000))
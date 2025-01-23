from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
from fastapi import HTTPException
from func.conf import DATABASE_URL
from db.model import Product


engine = create_async_engine(DATABASE_URL, echo=True)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Асинхронное добавление продукта в базу данных
async def add_product(db_session: AsyncSession, artikul: int, name: str, price: float, rating: float, stock: int):
    new_product = Product(
        artikul=artikul,
        name=name,
        price=price,
        rating=rating,
        stock=stock
    )

    db_session.add(new_product)
    try:
        await db_session.commit()  # Сохраняем изменения в базе данных
        return new_product
    except IntegrityError:
        await db_session.rollback()  # Если возникла ошибка, откатываем изменения
        raise HTTPException(status_code=500, detail="Failed to add product to the database")



async def get_product_by_artikul(db_session: AsyncSession, artikul: int):
    async with db_session.begin():
        result = await db_session.execute(select(Product).filter(Product.artikul == artikul))
        product = result.scalars().first()  # Получаем первый результат (если он есть)
    return product
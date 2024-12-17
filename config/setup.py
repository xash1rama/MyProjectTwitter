from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from database.models import engine, Base, User, session
from sqlalchemy.ext.asyncio import AsyncSession
from .conf_app import TEST_NAME
from sqlalchemy import select


@asynccontextmanager
async def lifespan(main_app: FastAPI):
    """
    Функция для создания пользователей при запуске приложения
    Так же запуск БД
    """

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

        await conn.run_sync(Base.metadata.create_all)
    try:
        async_session: AsyncSession = session()

        res = await async_session.execute(
            select(User).where(User.api_key == TEST_NAME.lower())
        )
        res_2 = await async_session.execute(
            select(User).where(User.api_key == TEST_NAME.lower() + "_2")
        )
        search = res.scalar_one_or_none()
        search_2 = res_2.scalar_one_or_none()
        if not search:
            user_test = User(api_key=TEST_NAME.lower(), name=TEST_NAME + " Frank")
            async_session.add(user_test)
        if not search_2:
            user_test2 = User(
                api_key=TEST_NAME.lower() + "_2", name=TEST_NAME + " Jozaf"
            )
            async_session.add(user_test2)
        await async_session.commit()

    except Exception as e:
        print(e)
    yield
    await engine.dispose()

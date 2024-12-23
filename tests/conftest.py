import pytest
from app import app
from httpx import AsyncClient
from database.models import init_db, Base, User, declarative_base
import pytest_asyncio
from typing import AsyncIterator
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="session")
async def test_db():
    os.environ[
        "DATABASE_URL"
    ] = "postgresql+asyncpg://test:test@postgres_container:5430/test_db"
    os.environ["ENV"] = "test"
    engine = create_async_engine(os.environ["DATABASE_URL"], echo=True)
    session = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        async_session: AsyncSession = session()

        new_user1 = User(name="Test Frank", api_key="test")
        async_session.add(new_user1)
        new_user2 = User(name="Test Jozaf", api_key="test_2")
        async_session.add(new_user2)
        async_session.refresh(new_user1)
        async_session.refresh(new_user1)
        async_session.commit()
        print("!" * 100, new_user1.name)
    yield async_session
    await engine.dispose()



@pytest.fixture(scope="session")
async def test_db():
    db_url = "postgresql+asyncpg://test:test@test_postgres:5432/test_tweet_db"
    engine, session = init_db(db_url)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session() as async_session:
        async with async_session.begin():
            user_test = User(api_key="test", name="Test Frank")
            user_test2 = User(api_key="test_2", name="Test Jozaf")
            async_session.add(user_test)
            async_session.add(user_test2)

        await async_session.commit()
        yield async_session

    await engine.dispose()


@pytest_asyncio.fixture()
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(base_url="http://localhost:8000") as c:
        yield c

@pytest.mark.asyncio
async def test_read_root(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_get_user_tweets(client: AsyncClient):
    """Тест получения твитов первого пользователя"""
    response = await client.get("/api/tweets", headers={"api-key": "test"})
    assert response.status_code == 200
    assert response.json()["result"] == True

@pytest.mark.asyncio
async def test_get_user_tweets_2(client: AsyncClient):
    """Тест получения твитов второго пользователя"""
    response = await client.get("/api/tweets", headers={"api-key": "test_2"})
    assert response.status_code == 200
    assert response.json()["result"] == True

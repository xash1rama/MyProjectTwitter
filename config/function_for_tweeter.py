import os
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import APIKeyHeader
from sqlalchemy.future import select
from fastapi import Depends, HTTPException
from .conf_app import PATH_IMAGE
from database.models import session, User, Follower, Media

header_api_key = APIKeyHeader(name="api-key")


async def get_session() -> AsyncSession:
    async with session() as async_session:
        yield async_session


async def get_client_token(api_key: str = Depends(header_api_key),
                           async_session: AsyncSession = Depends(get_session)):
    result = await async_session.execute(select(User.api_key))
    valid_api_keys = result.scalars().all()
    if api_key not in valid_api_keys:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key


async def get_following(id: int, async_session: AsyncSession = Depends(get_session)):
    try:
        # Запросна получение пользователей, на которых подписан пользователь с ID
        following_result = await async_session.execute(
            select(User)
            .select_from(Follower)
            .join(User, User.id == Follower.following_id)
            .where(Follower.follower_id == id)
        )
        following = following_result.scalars().all()
        print(f"Получены подписки для пользователя {id}: {following}")

        # Формируем список словарей для возврата
        return [{"id": follower.id, "name": follower.name} for follower in following] if following else []

    except Exception as e:
        print(f"Ошибка при получении пользователей, на которых подписан {id}: {str(e)}")
        return []



async def get_followers(user_id: int, async_session: AsyncSession = Depends(get_session)):
    try:
        followers_result = await async_session.execute(
            select(User)
            .select_from(Follower)
            .join(User, User.id == Follower.follower_id)
            .where(Follower.following_id == user_id)
        )

        followers = followers_result.scalars().all()
        print(f"Получены подписчики для пользователя {user_id}: {followers}")
        return [{"id": follower.id, "name": follower.name} for follower in followers] if followers else []

    except Exception as e:
        print(f"Oшибка при получении подписчиков пользователя {user_id}: {str(e)}")
        return []


async def delete_media(id:int, async_session: AsyncSession = Depends(get_session)):
    media = await async_session.execute(select(Media).where(Media.tweet_id == id))
    file = media.scalar_one_or_none()
    file_path = os.path.join(PATH_IMAGE, file.filename)
    os.remove(file_path)


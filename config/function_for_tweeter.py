import os
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import APIKeyHeader
from sqlalchemy.future import select
from fastapi import Depends, HTTPException
from .conf_app import PATH_IMAGE
from database.models import session, User, Follower, Media

header_api_key = APIKeyHeader(name="api-key")


async def get_session() -> AsyncSession:
    """
    Создание сессии базы данных
    """
    async with session() as async_session:
        yield async_session


async def get_client_token(
    api_key: str = Depends(header_api_key),
    async_session: AsyncSession = Depends(get_session),
):
    """
    Принимает и проверяет получаемый хедер
    :param api_key: индефикатор пользователя
    :param async_session: сессия бд
    :return: api_key
    """
    result = await async_session.execute(select(User.api_key))
    valid_api_keys = result.scalars().all()
    if api_key not in valid_api_keys:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key


async def get_following(id: int, async_session: AsyncSession = Depends(get_session)):
    """
    Запросна получение пользователей, на которых подписан пользователь с ID
    :param api_key: индефикатор пользователя
    :param async_session: сессия бд
    :return: list|[]
    """
    try:
        following_result = await async_session.execute(
            select(User)
            .select_from(Follower)
            .join(User, User.id == Follower.following_id)
            .where(Follower.follower_id == id)
        )
        following = following_result.scalars().all()
        return (
            [{"id": follower.id, "name": follower.name} for follower in following]
            if following
            else []
        )

    except Exception as e:
        return []


async def get_followers(
    user_id: int, async_session: AsyncSession = Depends(get_session)
):
    """
    Функция для полечения подписчиков
    :param user_id: получение id пользователя
    :param async_session: сессия бд
    :return: list|[]
    """
    try:
        followers_result = await async_session.execute(
            select(User)
            .select_from(Follower)
            .join(User, User.id == Follower.follower_id)
            .where(Follower.following_id == user_id)
        )

        followers = followers_result.scalars().all()
        return (
            [{"id": follower.id, "name": follower.name} for follower in followers]
            if followers
            else []
        )

    except Exception as e:
        return []


async def delete_media(id: int, async_session: AsyncSession = Depends(get_session)):
    """
    Функия для удаления медиа по id
    :param id: ID медиа
    :param async_session: сессия бд
    :return: None
    """
    media = await async_session.execute(select(Media).where(Media.tweet_id == id))
    file = media.scalar_one_or_none()
    file_path = os.path.join(PATH_IMAGE, file.filename)
    os.remove(file_path)

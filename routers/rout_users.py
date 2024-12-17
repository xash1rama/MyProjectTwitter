from fastapi.exceptions import HTTPException

from fastapi import APIRouter, Depends
from schemas.schemas import (
    ResultUserInfoModelOut,
    ErrorModel,
    UserInfoModel,
    ResultModel,
)
from sqlalchemy.ext.asyncio import AsyncSession
from config.function_for_tweeter import (
    get_session,
    get_following,
    get_followers,
    get_client_token,
)
from database.models import User, Follower
from sqlalchemy.future import select


router = APIRouter(tags=["user"])


@router.get("/api/users/me", response_model=ResultUserInfoModelOut | ErrorModel)
async def get_current_user(
    api_key: str = Depends(get_client_token),
    async_session: AsyncSession = Depends(get_session),
):
    """
    Пользователь может получить информацию о своём профиле:
    """
    try:
        result = await async_session.execute(
            select(User).where(User.api_key == api_key)
        )
        user = result.scalar_one_or_none()
        followers = await get_followers(user.id, async_session)
        following = await get_following(user.id, async_session)
        user_info = UserInfoModel(
            id=user.id, name=user.name, followers=followers, following=following
        )
        return ResultUserInfoModelOut(result=True, user=user_info)

    except Exception as er:
        return ErrorModel(
            result=False,
            error_type=str(type(er).__name__),
            error_message=str(er),
        )


@router.get("/api/users/{id}", response_model=ResultUserInfoModelOut | ErrorModel)
async def account_with_id(id: int, async_session: AsyncSession = Depends(get_session)):
    """
    Пользователь может получить информацию о произвольном профиле по его Id
    :param id:int Получение id Пользователя
    :param api_key:str Получение ключа (Имитация сессии)
    :return:dict
    """
    try:
        account_result = await async_session.execute(select(User).where(User.id == id))
        user = account_result.scalar_one_or_none()
        followers = await get_followers(id, async_session)
        following = await get_following(id, async_session)
        user_info = UserInfoModel(
            id=user.id, name=user.name, followers=followers, following=following
        )
        return ResultUserInfoModelOut(result=True, user=user_info)
    except Exception as er:
        return ErrorModel(
            result=False,
            error_type=str(type(er).__name__),
            error_message=str(er),
        )


@router.delete("/api/users/{id}/follow", response_model=ErrorModel | ResultModel)
async def unfollow(
    id: int,
    api_key: str = Depends(get_client_token),
    async_session: AsyncSession = Depends(get_session),
):
    """
    Пользователь может убрать подписку на другого пользователя.
    :param id:int Получение id Пользователя
    :param api_key:str Получение ключа (Имитация сессии)
    :return:dict  В ответ должно вернуться сообщение о статусе операции.
    """
    try:
        result = await async_session.execute(
            select(User).where(User.api_key == api_key)
        )
        user = result.scalar_one_or_none()
        unfollower = await async_session.execute(
            select(Follower).where(
                Follower.following_id == id, Follower.follower_id == user.id
            )
        )
        result = unfollower.scalar_one_or_none()
        await async_session.delete(result)
        await async_session.commit()
        return ResultModel(result=True)

    except Exception as er:
        return ErrorModel(
            result=False,
            error_type=str(type(er).__name__),
            error_message=str(er),
        )


@router.post("/api/users/{id}/follow")
async def follow(
    id: int,
    api_key: str = Depends(get_client_token),
    async_session: AsyncSession = Depends(get_session),
):
    """
    Пользователь может зафоловить другого пользователя.
    :param id:int Получение id Пользователя
    :param api_key:str Получение ключа (Имитация сессии)
    :return:dict  В ответ должно вернуться сообщение о статусе операции.
    """
    try:
        my_account = await async_session.execute(
            select(User).where(User.api_key == api_key)
        )
        user = my_account.scalar_one_or_none()
        follow = Follower(follower_id=user.id, following_id=id)
        async_session.add(follow)
        await async_session.commit()
        return ResultModel(result=True)

    except Exception as er:
        return ErrorModel(
            result=False,
            error_type=str(type(er).__name__),
            error_message=str(er),
        )

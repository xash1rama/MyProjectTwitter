from fastapi import APIRouter, Depends, HTTPException
from config.function_for_tweeter import get_client_token, get_session
from database.models import User, Like, Tweet, Media
from schemas.schemas import (
    TweetAdd,
    TweetCreate,
    ErrorModel,
    ResultModel,
    ResultTweetsModel,
)
from sqlalchemy.future import select
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from config.conf_app import PATH_IMAGE
import os

router = APIRouter(tags=["tweet"])


@router.post("/api/tweets", response_model=TweetAdd | ErrorModel)
async def tweets(
    tweet: TweetCreate,
    api_key: str = Depends(get_client_token),
    async_session: AsyncSession = Depends(get_session),
):
    """
    Запросом на этот endpoint пользователь будет создавать новый твит.
    Бэкенд будет его валидировать и сохранять в базу.
    :param api_key:str Получение ключа (Имитация сессии)
    :return:dict  В ответ должен вернуться id созданного твита.
    """
    try:
        result = await async_session.execute(
            select(User).where(User.api_key == api_key)
        )
        id_user = result.scalar_one_or_none()
        new_tweet = Tweet(tweet_data=str(tweet.tweet_data), user_id=id_user.id)
        async_session.add(new_tweet)
        await async_session.commit()
        await async_session.refresh(new_tweet)
        for media_id in tweet.tweet_media_ids:
            media = await async_session.execute(
                select(Media).where(Media.id == media_id)
            )
            media_instance = media.scalar_one_or_none()
            if media_instance:
                media_instance.tweet_id = new_tweet.id
                async_session.add(media_instance)
        await async_session.commit()

        return TweetAdd(result=True, tweet_id=new_tweet.id)
    except Exception as er:
        return ErrorModel(
            result=False,
            error_type=str(type(er).__name__),
            error_message=str(er),
        )


@router.delete("/api/tweets/{id}", response_model=ErrorModel | ResultModel)
async def delete_tweet(
    id: int,
    api_key: str = Depends(get_client_token),
    async_session: AsyncSession = Depends(get_session),
):
    """
    Пользователь может удалить твит.
    :param id: int Получение id твита
    :param api_key: str Получение ключа (Имитация сессии)
    :return: dict В ответ должно вернуться сообщение о статусе операции.
    """
    try:
        result = await async_session.execute(
            select(User).where(User.api_key == api_key)
        )
        id_user = result.scalar_one_or_none()
        if id_user is None:
            raise HTTPException(status_code=403, detail="Invalid API key.")

        tweet = await async_session.execute(
            select(Tweet).where(Tweet.id == id, Tweet.user_id == id_user.id)
        )
        tweet_instance = tweet.scalar_one_or_none()

        if tweet_instance is None:
            raise HTTPException(status_code=404, detail="Tweet not found")

        media = await async_session.execute(select(Media).where(Media.tweet_id == id))
        file = media.scalar_one_or_none()

        await async_session.delete(tweet_instance)
        await async_session.commit()
        if file:
            file_path = os.path.join(PATH_IMAGE, file.filename)
            if os.path.exists(file_path):
                os.remove(file_path)

        return ResultModel(result=True)

    except Exception as er:
        return ErrorModel(
            result=False,
            error_type=str(type(er).__name__),
            error_message=str(er),
        )


@router.post("/api/tweets/{id}/likes", response_model=ResultModel | ErrorModel)
async def like(
    id: int,
    api_key: str = Depends(get_client_token),
    async_session: AsyncSession = Depends(get_session),
):
    """
    Пользователь может поставить отметку «Нравится» на твит.
    :param id:int Получение id Твита
    :param api_key:str Получение ключа (Имитация сессии)
    :return:dict  В ответ должно вернуться сообщение о статусе операции.
    """
    try:
        result = await async_session.execute(
            select(User).where(User.api_key == api_key)
        )
        user = result.scalar_one_or_none()
        like = Like(user_id=user.id, tweet_id=id)
        async_session.add(like)
        await async_session.commit()
        return ResultModel(result=True)

    except Exception as er:
        return ErrorModel(
            result=False,
            error_type=str(type(er).__name__),
            error_message=str(er),
        )


@router.delete("/api/tweets/{id}/likes", response_model=ResultModel | ErrorModel)
async def delete_like(
    id: int,
    api_key: str = Depends(get_client_token),
    async_session: AsyncSession = Depends(get_session),
):
    """
    Пользователь может убрать отметку «Нравится» с твита.
    :param id:int Получение id Твита
    :param api_key:str Получение ключа (Имитация сессии)
    :return:dict  В ответ должно вернуться сообщение о статусе операции.
    """
    try:
        result = await async_session.execute(
            select(User).where(User.api_key == api_key)
        )
        user = result.scalar_one_or_none()
        await async_session.execute(
            delete(Like).where(Like.tweet_id == id, Like.user_id == user.id)
        )
        await async_session.commit()
        return ResultModel(result=True)

    except Exception as er:
        return {
            "result": False,
            "error_type": str(type(er).__name__),
            "error_message": str(er),
        }


@router.get("/api/tweets", response_model=ResultTweetsModel | ErrorModel)
async def get_user_tweets(async_session: AsyncSession = Depends(get_session)):
    """
    Ендпоинт для получения всех твитов
    """
    try:
        result = await async_session.execute(
            select(
                Tweet.id.label("tweet_id"),
                Tweet.tweet_data.label("content"),
                Media.id.label("media_id"),
                Tweet.user_id.label("author_id"),
                User.name.label("author_name"),
            )
            .outerjoin(Media, Media.tweet_id == Tweet.id)
            .outerjoin(User, User.id == Tweet.user_id)
            .order_by(Tweet.time.desc())
        )
        tweets = result.fetchall()
        tweets_output = []
        for tweet in tweets:
            print(type(tweet[0]))
            result = await async_session.execute(
                select(User.id, User.name)
                .join(Like, Like.user_id == User.id)
                .where(Like.tweet_id == int(tweet[0]))
            )
            likes = result.fetchall()
            tweets_output.append(
                {
                    "id": int(tweet[0]),
                    "content": tweet[1],
                    "attachments": [f"/api/medias/{int(tweet[2])}"]
                    if tweet.media_id
                    else [],
                    "author": {"id": int(tweet[3]), "name": tweet[4]},
                    "likes": [
                        {"user_id": liker[0], "name": liker[1]} for liker in likes
                    ],
                }
            )
        return ResultTweetsModel(result=True, tweets=tweets_output)

    except Exception as er:
        return ErrorModel(
            result=False,
            error_type=str(type(er).__name__),
            error_message=str(er),
        )

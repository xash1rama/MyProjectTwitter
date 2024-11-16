from os import write

import uvicorn
from database.database import engine, session, Base
from database.models import User, Tweet, Like, Media, Follower
from sqlalchemy import delete, join, outerjoin, desc
from sqlalchemy.future import select
from fastapi import FastAPI, Header, Depends, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from starlette.staticfiles import StaticFiles
import aiofiles
from schemas.schemas import TweetCreate

app = FastAPI()

app.mount("/", StaticFiles(directory="static"), name="static")

API_KEY_NOW = ""
TEST_NAME = "Test"
PATH_IMAGE = f"static/images/"

async def get_client_token(api_key: str = Header(...)):
    if api_key != "expected_token" and API_KEY_NOW == "":
        raise HTTPException(status_code=400, detail="Invalid Api Key")
    api_key_now = api_key
    return api_key_now


@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with session() as sync_ses:
        user_test = User()
        user_test.api_key = TEST_NAME
        user_test.name = TEST_NAME + " Frank"
        api_key_now = TEST_NAME

@app.on_event("shutdown")
async def shutdown_event():
    async with session() as sync_ses:
        query = sync_ses.delete(User).were(User.api_key==TEST_NAME)
        sync_ses.execute(query)
    await session.close()
    await engine.dispose()


@app.post("/api/tweets")
async def tweets(tweet: TweetCreate, api_key: str = Depends(get_client_token)):
    """
        Запросом на этот endpoint пользователь будет создавать новый твит.
        Бэкенд будет его валидировать и сохранять в базу.
        :param api_key:str Получение ключа (Имитация сессии)
        :return:dict  В ответ должен вернуться id созданного твита.
    """
    try:
        async with session() as async_session:
            id_user = await async_session.execute(select(User).where(User.api_key==api_key)).scalar_one()
            new_tweet = Tweet(tweet_data=tweet.tweet_data, tweet_media_ids=tweet.tweet_media_ids, user_id=id_user)
            await async_session.add(new_tweet)
            await async_session.commit()
        result = {
                "result": True,
                "tweet_id": new_tweet.id
                 }
        return result
    except Exception as er:
        return {
            "result": False,
            "error_type": str(type(er).__name__),
            "error_message": str(er)
        }


@app.post("/api/medias")
async def tweets(file: UploadFile = File(...), api_key: str = Depends(get_client_token)):
    """
        Endpoint для загрузки файлов из твита. Загрузка происходит через
        отправку формы.
        :param api_key:str Получение ключа (Имитация сессии)
        :return:dict  В ответ должно вернуться сообщение о статусе операции.
    """
    try:
        async with session() as async_session:
            last_id = await async_session.execute(select(Media.id).order_by(Media.id.desc()).limit(1)).scalar_one_or_none()
            await async_session.commit()
        if last_id is not None:
            filename = f"{api_key + file.filename + str(last_id + 1)}"

        else:
            filename = f"{api_key + file.filename + str(last_id)}1"
            
        contents = await file.read()
        async with aiofiles.open(PATH_IMAGE+filename, "wb") as file_save:
            await file_save.write(contents)

        async with session() as async_session:
            safe_image = Media(filename=filename)
            last_id = await async_session.execute(select(Media.id).order_by(Media.id.desc()).limit(1)).scalar_one_or_none()
            await async_session.add(safe_image)
            await async_session.commit()
        result = {
                 "result": True,
                 "media_id": last_id
                 }
        return result

    except Exception as er:
        return {
            "result": False,
            "error_type": str(type(er).__name__),
            "error_message": str(er)
        }


@app.delete("/api/tweets/<id>")
async def delete_tweet(id: int, api_key: str = Depends(get_client_token)):
    """
        Пользователь может Удалить Твит.
        :param id:int Получение id Твита
        :param api_key:str Получение ключа (Имитация сессии)
        :return:dict  В ответ должно вернуться сообщение о статусе операции.
        """
    try:
        async with session() as async_session:
            tweet = await async_session.execute(select(Tweet).where(Tweet.id == id))
            tweet = tweet.scalar_one_or_none()
            if tweet is None:
                raise HTTPException(status_code=404, detail="Tweet not found")
            await async_session.execute(delete(Tweet).where(Tweet.id == id))
            await async_session.commit()
        result = {
                "result": True
                }
        return result
    except Exception as er:
        return {
            "result": False,
            "error_type": str(type(er).__name__),
            "error_message": str(er)
        }


@app.post("/api/tweets/<id>/likes")
async def like(id: int, api_key: str = Depends(get_client_token)):
    """
        Пользователь может поставить отметку «Нравится» на твит.
        :param id:int Получение id Твита
        :param api_key:str Получение ключа (Имитация сессии)
        :return:dict  В ответ должно вернуться сообщение о статусе операции.
        """
    try:
        async with session() as async_session:
            id_user = await async_session.execute(select(User.id).where(User.id==api_key)).scalar_one()
            like = Like(user_id=id_user, tweet_id=id)
            await async_session.add(like)
            await async_session.commit()
        result = {
            "result": True
        }
        return result

    except Exception as er:
        return {
            "result": False,
            "error_type": str(type(er).__name__),
            "error_message": str(er)
            }


@app.delete("/api/tweets/<id>/likes")
async def delete_like(id: int, api_key: str = Depends(get_client_token)):
    """
        Пользователь может убрать отметку «Нравится» с твита.
        :param id:int Получение id Твита
        :param api_key:str Получение ключа (Имитация сессии)
        :return:dict  В ответ должно вернуться сообщение о статусе операции.
    """
    try:
        async with session() as async_session:
            await async_session.execute(delete(Like).where(Like.tweet_id==id))
            await async_session.commit()
        result = {
                "result": True
                }
        return result

    except Exception as er:
        return {
            "result": False,
            "error_type": str(type(er).__name__),
            "error_message": str(er)
        }


@app.post("/api/users/<id>/follow")
async def follow(id: int, api_key: str = Depends(get_client_token)):
    """
        Пользователь может зафоловить другого пользователя.
        :param id:int Получение id Пользователя
        :param api_key:str Получение ключа (Имитация сессии)
        :return:dict  В ответ должно вернуться сообщение о статусе операции.
    """
    try:
        async with session() as async_session:
            my_account = await async_session.execute(select(User.id).where(User.api_key==api_key)).scalar_one()
            follow = Follower(follower_id=id, following_id=my_account)
            async_session.add(follow)
            await async_session.commit()
        result = {
            "result": True
        }
        return result

    except Exception as er:
        return {
            "result": False,
            "error_type": str(type(er).__name__),
            "error_message": str(er)
        }


@app.delete("/api/users/<id>/follow")
async def unfollow(id: int, api_key: str = Depends(get_client_token)):
    """
        Пользователь может убрать подписку на другого пользователя.
        :param id:int Получение id Пользователя
        :param api_key:str Получение ключа (Имитация сессии)
        :return:dict  В ответ должно вернуться сообщение о статусе операции.
    """
    try:
        async with session() as async_session:
            my_account = await async_session.execute(select(User.id).where(User.api_key==api_key)).scalar_one()
            await async_session.execute(delete(Follower).where(Follower.follower_id==id, Follower.following_id==my_account)).scalar_one()
            await async_session.commit()
        result = {
                "result": True
                }
        return result

    except Exception as er:
        return {
            "result": False,
            "error_type": str(type(er).__name__),
            "error_message": str(er)
        }


@app.get("/api/tweets")
async def all_tweets(api_key: str = Depends(get_client_token)):
    """
        Пользователь может получить ленту с твитами.
        :param api_key:str Получение ключа (Имитация сессии)
        :return:dict
        В ответ должен вернуться json со списком твитов для ленты этого
        пользователя.
    """
    try:
        async with (session() as async_session):
            my_account = await async_session.execute(select(User.id).where(User.api_key==api_key)).scalar_one()
            all_tweets_select = await async_session.execute(
                select(
                    Tweet.id.label("id"),
                    Tweet.tweet_data.label("content"),
                    Tweet.tweet_media_ids.label("attachments"),
                    User.id.label("user_id"),
                    User.name.label("name"),
                    Like.user_id.label("like_user_id"),
                    Like.user_like.name.label("likes_name")
                ).where()
                .join(User, User.id == Tweet.user_id)
                .outerjoin(Like, Like.tweet_id == Tweet.id).order_by(desc(Tweet.time))
            )

            result = {
                    "result": True,
                    "tweets": []
                    }
            for tweet in all_tweets_select:
                tweet_info = {
                                "id": tweet.id,
                                "content": tweet.id,
                                "attachments": tweet.connect,
                                "author": {
                                    "id": tweet.user_id,
                                    "name": tweet.name
                                    },
                                "likes": []
                              }
                if tweet.like_user_id:
                    tweet_info["likes"].append({
                        "user_id": tweet.like_user_id,
                        "name": tweet.likes_name
                    })
                result["tweets"].append(tweet_info)
            await async_session.commit()
        return result

    except Exception as er:
        return {
            "result": False,
            "error_type": str(type(er).__name__),
            "error_message": str(er)
        }


@app.get("/api/users/me")
async def my_account(api_key: str = Depends(get_client_token)):
    """
        Пользователь может получить информацию о своём профиле
        :param api_key:str Получение ключа (Имитация сессии)
        :return:dict
    """
    try:
        async with session() as async_session:
            my_account_id = await async_session.execute(select(User.id).where(User.api_key==api_key)).scalar_one()
            my_account = await async_session.execute(
                select(
                    User.id.label("id"),
                    User.name.label("name"),
                    Follower.users_follower.id.label("follower_id"),
                    Follower.users_follower.name.label("follower_name"),
                    Follower.users_following.id.label("following_id"),
                    Follower.users_following.name.label("following_name")
                ).where(User.id == my_account_id)
                .join(Follower, Follower.follower_id == User.id)
            .outerjoin(User, User.id == Follower.following_id)
            .order_by(desc(Follower.time)))
            result = {
                "result": True,
                "user": {
                    "id": my_account.id,
                    "name": my_account.name,
                    "followers": [{"id": follower.follower_id, "name": follower.follower_name} for follower in my_account],
                    "following": [{"id": following.following_id, "name": following.following_name} for following in my_account]
                }
            }
            await async_session.commit()
        return result
    except Exception as er:
        return {
            "result": False,
            "error_type": str(type(er).__name__),
            "error_message": str(er)
        }


@app.get("/api/users/{id}")
async def account_with_id(id: int, api_key: str = Depends(get_client_token)):
    """
        Пользователь может получить информацию о произвольном профиле по его Id
        :param id:int Получение id Пользователя
        :param api_key:str Получение ключа (Имитация сессии)
        :return:dict
    """
    try:
        async with session() as async_session:
            my_account_id = await async_session.execute(select(User.id).where(User.api_key == api_key)).scalar_one()
            my_account = await async_session.execute(
                select(
                    User.id.label("id"),
                    User.name.label("name"),
                    Follower.users_follower.id.label("follower_id"),
                    Follower.users_follower.name.label("follower_name"),
                    Follower.users_following.id.label("following_id"),
                    Follower.users_following.name.label("following_name")
                ).where(User.id == id)
                .join(Follower, Follower.follower_id == User.id)
                .outerjoin(User, User.id == Follower.following_id)
                .order_by(desc(Follower.time)))
            result = {
                "result": True,
                "user": {
                    "id": my_account.id,
                    "name": my_account.name,
                    "followers": [{"id": follower.follower_id, "name": follower.follower_name} for follower in
                                  my_account],
                    "following": [{"id": following.following_id, "name": following.following_name} for following in
                                  my_account]
                }
            }
            await async_session.commit()
        return result

    except Exception as er:
        return {
            "result": False,
            "error_type": str(type(er).__name__),
            "error_message": str(er)
        }


if __name__ == "__main__":
    uvicorn.run("app:app")
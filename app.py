from fileinput import filename

import uvicorn
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from pathlib import Path
from database.models import User, Tweet, Like, Media, Follower, engine, session, Base
from sqlalchemy import delete, desc
from sqlalchemy.future import select
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Response
import aiofiles

from schemas.schemas import TweetCreate, ResultUserInfoModelOut,GetTweets, TweetAdd, MediaModel, UserInfoModel, ErrorModel, TweetModel, ResultTweetsModel
from function_for_tweeter import  get_session, get_client_token, get_following, get_followers
from conf_app import PATH_IMAGE, API_KEY_NOW, TEST_NAME
app = FastAPI()




app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        async with session() as sync_ses:
            res = await sync_ses.execute(select(User).where(User.api_key == TEST_NAME.lower()))
            res_2 = await sync_ses.execute(select(User).where(User.api_key == TEST_NAME.lower() + "_2"))
            search = res.scalar_one_or_none()
            search_2 = res_2.scalar_one_or_none()

            if not search:
                user_test = User(api_key=TEST_NAME.lower(), name=TEST_NAME + " Frank")
                sync_ses.add(user_test)
                await sync_ses.commit()

                new_tweet = Tweet(tweet_data="Тестовый репост для отображения на сайте.",
                                  user_id=user_test.id)
                sync_ses.add(new_tweet)
                await sync_ses.commit()

                new_media = Media(filename=PATH_IMAGE+"test_3_Treehouse_of_Horror_XII.gif", tweet_id=new_tweet.id)
                sync_ses.add(new_media)
                await sync_ses.commit()

            if not search_2:
                user_test2 = User(api_key=TEST_NAME.lower()+ "_2" , name=TEST_NAME + " Jozaf")
                sync_ses.add(user_test2)
                await sync_ses.commit()

                follower = Follower(follower_id = user_test.id, following_id=user_test2.id)
                sync_ses.add(follower)
                await sync_ses.commit()

                new_tweet = Tweet(tweet_data="Тестовый репост для отображения на сайте 2.",
                                  user_id=user_test.id,)
                sync_ses.add(new_tweet)
                await sync_ses.commit()

    except Exception as e:
        print(e)


@app.on_event("shutdown")
async def shutdown_event():
    try:
        async with session() as async_sess:
            async with async_sess.begin():
                result = await async_sess.execute(select(User).where(User.api_key == TEST_NAME.lower()))
                user = result.scalar_one_or_none()
                if user:
                    await async_sess.execute(delete(Tweet).where(Tweet.user_id == user.id))
                    await async_sess.execute(delete(User).where(User.api_key == TEST_NAME.lower()))
                    await async_sess.commit()

    except Exception as e:
        print(e)
    finally:
        await engine.dispose()


@app.get("/", response_class=HTMLResponse)
async def read_root():
    file_path = Path("static/index.html")
    return HTMLResponse(content=file_path.read_text(), status_code=200)



@app.post("/api/tweets", response_model=TweetAdd)
async def tweets(tweet:TweetCreate, api_key: str = Depends(get_client_token), async_session: AsyncSession = Depends(get_session)):
    """
    Запросом на этот endpoint пользователь будет создавать новый твит.
    Бэкенд будет его валидировать и сохранять в базу.
    :param api_key:str Получение ключа (Имитация сессии)
    :return:dict  В ответ должен вернуться id созданного твита.
    """
    print(tweet)
    try:
        result = await async_session.execute(
            select(User).where(User.api_key==api_key)
        )
        id_user = result.scalar_one_or_none()
        new_tweet = Tweet(
            tweet_data=str(tweet.tweet_data),
            user_id=id_user.id
        )
        async_session.add(new_tweet)
        await async_session.commit()
        await async_session.refresh(new_tweet)
        for media_id in tweet.tweet_media_ids:
            media = await async_session.execute(select(Media).where(Media.id == media_id))
            media_instance = media.scalar_one_or_none()
            if media_instance:
                media_instance.tweet_id = new_tweet.id
                async_session.add(media_instance)
        await async_session.commit()

        return {"result":True, "tweet_id":new_tweet.id}
    except Exception as er:
        return ErrorModel(
            result=False,
            error_type=str(type(er).__name__),
            error_message=str(er),
        )


@app.post("/api/medias", response_model=MediaModel)
async def upload_media(file: UploadFile = File(...), api_key: str = Depends(get_client_token), async_session: AsyncSession = Depends(get_session)):
    try:
        last_id_result = await async_session.execute(
            select(Media.id).order_by(Media.id.desc()).limit(1)
        )
        last_id = last_id_result.scalar_one_or_none()

        filename = f"{api_key}_{(last_id + 1) if last_id is not None else 1}_{file.filename}"

        contents = await file.read()
        async with aiofiles.open(PATH_IMAGE + filename, "wb") as file_save:
            await file_save.write(contents)

        safe_image = Media(filename=filename)
        print("*" * 10, safe_image.to_json())
        async_session.add(safe_image)
        await async_session.commit()
        return MediaModel(result=True, media_id=safe_image.id)

    except Exception as er:
        return {
            "result": False,
            "error_type": str(type(er).__name__),
            "error_message": str(er),
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
        result = {"result": True}
        return result
    except Exception as er:
        return {
            "result": False,
            "error_type": str(type(er).__name__),
            "error_message": str(er),
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
            id_user = await async_session.execute(
                select(User.id).where(User.id == api_key)
            ).scalar_one()
            like = Like(user_id=id_user, tweet_id=id)
            await async_session.add(like)
            await async_session.commit()
        result = {"result": True}
        return result

    except Exception as er:
        return {
            "result": False,
            "error_type": str(type(er).__name__),
            "error_message": str(er),
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
            await async_session.execute(delete(Like).where(Like.tweet_id == id))
            await async_session.commit()
        result = {"result": True}
        return result

    except Exception as er:
        return {
            "result": False,
            "error_type": str(type(er).__name__),
            "error_message": str(er),
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
            my_account = await async_session.execute(
                select(User.id).where(User.api_key == api_key)
            ).scalar_one()
            follow = Follower(follower_id=id, following_id=my_account)
            async_session.add(follow)
            await async_session.commit()
        result = {"result": True}
        return result

    except Exception as er:
        return {
            "result": False,
            "error_type": str(type(er).__name__),
            "error_message": str(er),
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
            my_account = await async_session.execute(
                select(User.id).where(User.api_key == api_key)
            ).scalar_one()
            await async_session.execute(
                delete(Follower).where(
                    Follower.follower_id == id, Follower.following_id == my_account
                )
            ).scalar_one()
            await async_session.commit()
        result = {"result": True}
        return result

    except Exception as er:
        return {
            "result": False,
            "error_type": str(type(er).__name__),
            "error_message": str(er),
        }



@app.get("/api/tweets", response_model=ResultTweetsModel|ErrorModel)
async def get_user_tweets(api_key: str = Depends(get_client_token), async_session: AsyncSession = Depends(get_session)):
    """
    Получает твиты текущего пользователя и информацию о его подписчиках.
    """
    try:
        result = await async_session.execute(
            select(User).where(User.api_key == api_key)
        )
        user = result.scalar_one_or_none()
        result = await async_session.execute(
            select(Tweet).where(Tweet.user_id == user.id)
        )
        tweets = result.scalars().all()
        followers = user.followers
        tweets_output = []

        for tweet in tweets:
            tweet_info = {
                "id": tweet.id,
                "content": tweet.tweet_data,
                "attachments": [f"/api/medias/{media.id}" for media in tweet.medias],
                "author": {
                    "id": tweet.user_tweet.id,
                    "name": tweet.user_tweet.name
                },
                "likes": [
                    {
                        "user_id": like.user_like.id,
                        "name": like.user_like.name
                    }
                    for like in tweet.likes
                ]
            }
            tweets_output.append(tweet_info)

        return ResultTweetsModel(result=True, tweets=tweets_output)

    except Exception as er:
        return {
            "result":False,
            "error_type":str(type(er).__name__),
            "error_message":str(er),
        }

@app.get("/api/medias/{id}")
async def get_image(id:int, async_session: AsyncSession = Depends(get_session)):
    result = await async_session.execute(
        select(Media.filename).where(Media.id==id)
    )
    image_path = result.scalar_one()
    try:
        async with aiofiles.open(PATH_IMAGE+image_path, mode='rb') as file:
            image_bytes = await file.read()
        return Response(content=image_bytes,
                        media_type="image/jpeg")
    except FileNotFoundError:
        return Response(status_code=404, content="Image not found")


@app.get("/api/users/me", response_model=ResultUserInfoModelOut)
async def get_current_user(api_key: str = Depends(get_client_token), async_session: AsyncSession = Depends(get_session)):
    try:
        result = await async_session.execute(
            select(User).where(User.api_key == api_key)
        )
        user = result.scalar_one()

        followers = await get_followers(user.id, async_session)
        following = await get_following(user.id, async_session)

        user_info = UserInfoModel(
            id=user.id,
            name=user.name,
            followers=followers,
            following=following,
        )
        print(user_info)
        return {"result":True, "user":user_info}

    except Exception as er:
        return ErrorModel(
            result=False,
            error_type=str(type(er).__name__),
            error_message=str(er),
        )

@app.get("/api/users/{id}", response_model=ResultUserInfoModelOut)
async def account_with_id(id: int, async_session: AsyncSession = Depends(get_session)):
    """
    Пользователь может получить информацию о произвольном профиле по его Id
    :param id:int Получение id Пользователя
    :param api_key:str Получение ключа (Имитация сессии)
    :return:dict
    """
    try:
        result = await async_session.execute(
                select(
                    User.id.label("id"),
                    User.name.label("name"),
                    Follower.users_follower.id.label("follower_id"),
                    Follower.users_follower.name.label("follower_name"),
                    Follower.users_following.id.label("following_id"),
                    Follower.users_following.name.label("following_name"),
                )
                .where(User.id == id)
                .join(Follower, Follower.follower_id == User.id)
                .outerjoin(User, User.id == Follower.following_id)
                .order_by(desc(Follower.time))
            )
        account_uses = result.scalar_one()
        return ResultUserInfoModelOut(result=True, user=account_uses)

    except Exception as er:
        return ErrorModel(
            result = False,
            error_type = str(type(er).__name__),
            error_message = str(er),
        )


if __name__ == "__main__":
    uvicorn.run("app:app")

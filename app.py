import os
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from pathlib import Path
from sqlalchemy import delete
from sqlalchemy.future import select
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Response
import aiofiles

from database.models import User, Tweet, Like, Media, Follower
from schemas.schemas import TweetCreate, ResultUserInfoModelOut, TweetAdd, MediaModel, UserInfoModel, ErrorModel, \
    ResultTweetsModel, ResultModel
from function_for_tweeter import  get_session, get_client_token, get_following, get_followers
from conf_app import PATH_IMAGE



# @asynccontextmanager
# async def lifespan(main_app: FastAPI):
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)
#     try:
#         async with session() as sync_ses:
#             res = await sync_ses.execute(select(User).where(User.api_key == TEST_NAME.lower()))
#             res_2 = await sync_ses.execute(select(User).where(User.api_key == TEST_NAME.lower() + "_2"))
#             search = res.scalar_one_or_none()
#             search_2 = res_2.scalar_one_or_none()
#
#             if not search:
#                 user_test = User(api_key=TEST_NAME.lower(), name=TEST_NAME + " Frank")
#                 sync_ses.add(user_test)
#                 await sync_ses.commit()
#
#                 new_tweet = Tweet(tweet_data="Тестовый репост для отображения на сайте.",
#                                   user_id=user_test.id)
#                 sync_ses.add(new_tweet)
#                 await sync_ses.commit()
#
#                 new_media = Media(filename=PATH_IMAGE + "Treehouse_of_Horror_XII.gif", tweet_id=new_tweet.id)
#                 sync_ses.add(new_media)
#                 await sync_ses.commit()
#
#             if not search_2:
#                 user_test2 = User(api_key=TEST_NAME.lower() + "_2", name=TEST_NAME + " Jozaf")
#                 sync_ses.add(user_test2)
#                 await sync_ses.commit()
#
#                 follower = Follower(follower_id=user_test2.id, following_id=user_test.id)
#                 sync_ses.add(follower)
#                 await sync_ses.commit()
#
#                 new_tweet = Tweet(tweet_data="Тестовый репост для отображения на сайте 2.",
#                                   user_id=user_test2.id, )
#                 sync_ses.add(new_tweet)
#                 await sync_ses.commit()
#
#     except Exception as e:
#         print(e)
#     yield
#     try:
#         async with session() as async_sess:
#             async with async_sess.begin():
#                 await async_sess.execute(delete(Tweet))
#                 await async_sess.execute(delete(Follower))
#                 await async_sess.execute(delete(User))
#                 await async_sess.execute(delete(Media))
#                 await async_sess.execute(delete(Like))
#                 await async_sess.commit()
#
#     except Exception as e:
#         print(e)
#     finally:
#         await engine.dispose()


app = FastAPI()


app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/js", StaticFiles(directory="static/js"), name="js")
app.mount("/css", StaticFiles(directory="static/css"), name="css")
app.mount("/images", StaticFiles(directory="static/images"), name="image")



@app.get("/", response_class=HTMLResponse)
async def read_root():
    file_path = Path("static/index.html")
    return HTMLResponse(content=file_path.read_text(), status_code=200)



@app.post("/api/tweets", response_model=TweetAdd|ErrorModel)
async def tweets(tweet:TweetCreate, api_key: str = Depends(get_client_token), async_session: AsyncSession = Depends(get_session)):
    """
    Запросом на этот endpoint пользователь будет создавать новый твит.
    Бэкенд будет его валидировать и сохранять в базу.
    :param api_key:str Получение ключа (Имитация сессии)
    :return:dict  В ответ должен вернуться id созданного твита.
    """
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
        print(new_tweet.to_json())
        for media_id in tweet.tweet_media_ids:
            media = await async_session.execute(select(Media).where(Media.id == media_id))
            media_instance = media.scalar_one_or_none()
            if media_instance:
                media_instance.tweet_id = new_tweet.id
                async_session.add(media_instance)
        await async_session.commit()

        return TweetAdd(result = True, tweet_id = new_tweet.id)
    except Exception as er:
        print("!"*100)
        print("POST tweets")
        print(ErrorModel(
            result=False,
            error_type=str(type(er).__name__),
            error_message=str(er),
        ))
        return ErrorModel(
            result=False,
            error_type=str(type(er).__name__),
            error_message=str(er),
        )


@app.delete("/api/tweets/{id}", response_model=ErrorModel|ResultModel)
async def delete_tweet(id: int, api_key: str = Depends(get_client_token), async_session: AsyncSession = Depends(get_session)):
    """
    Пользователь может Удалить Твит.
    :param id:int Получение id Твита
    :param api_key:str Получение ключа (Имитация сессии)
    :return:dict  В ответ должно вернуться сообщение о статусе операции.
    """
    try:
        result = await async_session.execute(
            select(User).where(User.api_key==api_key)
        )
        id_user = result.scalar_one_or_none()
        tweet = await async_session.execute(select(Tweet).where(Tweet.id == id, Tweet.user_id==id_user.id))
        tweet = tweet.scalar_one_or_none()
        if tweet is None:
                raise HTTPException(status_code=404, detail="Tweet not found")
        media = await async_session.execute(select(Media).where(Media.tweet_id == id))
        file = media.scalar_one_or_none()

        await async_session.delete(tweet)
        await async_session.commit()
        file_path = os.path.join(PATH_IMAGE, file.filename)
        os.remove(file_path)

        return ResultModel(result = True)
    except Exception as er:
        return ErrorModel(
            result=False,
            error_type=str(type(er).__name__),
            error_message=str(er),
        )


@app.post("/api/medias", response_model=MediaModel|ErrorModel)
async def upload_media(
        file: UploadFile = File(...),
        api_key: str = Depends(get_client_token),
        async_session: AsyncSession = Depends(get_session),
):
    try:

        result = await async_session.execute(
            select(User).where(User.api_key == api_key)
        )
        id_user = result.scalar_one_or_none()
        last_id_result = await async_session.execute(
            select(Tweet.id).where(Tweet.user_id==id_user.id).order_by(Tweet.id.desc()).limit(1)
        )
        last_id = last_id_result.scalar_one_or_none()
        contents = await file.read()
        os.makedirs(PATH_IMAGE, exist_ok=True)

        file_name = "user_id:" + str(id_user.id) + "tweet_id:" + str(last_id) + file.filename

        file_path = os.path.join(PATH_IMAGE, file_name)
        async with aiofiles.open(file_path, "wb") as file_save:
            await file_save.write(contents)

        safe_image = Media(filename=file_name, tweet_id=last_id)
        async_session.add(safe_image)
        await async_session.commit()
        await async_session.refresh(safe_image)


        return MediaModel(result=True, media_id=safe_image.id)

    except Exception as er:
        print("!"*100)
        print("POST medias")
        print(ErrorModel(
            result=False,
            error_type=str(type(er).__name__),
            error_message=str(er),
        ))
        return ErrorModel(
            result = False,
            error_type = str(type(er).__name__),
            error_message = str(er),
        )


@app.get("/api/medias/{id}")
async def get_image(id:int, async_session: AsyncSession = Depends(get_session)):
    result = await async_session.execute(
        select(Media.filename).where(Media.id==id)
    )
    image_path = result.scalar_one_or_none()
    os.makedirs(PATH_IMAGE, exist_ok=True)
    file_path = os.path.join(PATH_IMAGE, image_path)
    try:
        async with aiofiles.open(file_path, mode='rb') as file:
            image_bytes = await file.read()
        return Response(content=image_bytes,
                        media_type="image/jpeg")

    except Exception as er:
        print("!"*100)
        print("GET medias/id")
        print(ErrorModel(
            result=False,
            error_type=str(type(er).__name__),
            error_message=str(er),
        ))
        return ErrorModel(
            result=False,
            error_type=str(type(er).__name__),
            error_message=str(er),
        )


@app.post("/api/tweets/{id}/likes")
async def like(id: int, api_key: str = Depends(get_client_token), async_session: AsyncSession = Depends(get_session)):
    """
    Пользователь может поставить отметку «Нравится» на твит.
    :param id:int Получение id Твита
    :param api_key:str Получение ключа (Имитация сессии)
    :return:dict  В ответ должно вернуться сообщение о статусе операции.
    """
    try:
        result = await async_session.execute(
            select(User).where(User.api_key == api_key))
        user = result.scalar_one_or_none()
        like = Like(user_id=user.id, tweet_id=id)
        async_session.add(like)
        await async_session.commit()
        return ResultModel(result = True)

    except Exception as er:
        print("!" * 100)
        print("POST tweets LIKE")
        print(ErrorModel(
            result=False,
            error_type=str(type(er).__name__),
            error_message=str(er),
        ))
        return ErrorModel(
            result=False,
            error_type=str(type(er).__name__),
            error_message=str(er),
        )


@app.delete("/api/tweets/{id}/likes")
async def delete_like(id: int, api_key: str = Depends(get_client_token), async_session: AsyncSession = Depends(get_session)):
    """
    Пользователь может убрать отметку «Нравится» с твита.
    :param id:int Получение id Твита
    :param api_key:str Получение ключа (Имитация сессии)
    :return:dict  В ответ должно вернуться сообщение о статусе операции.
    """
    try:
        result = await async_session.execute(
            select(User).where(User.api_key == api_key))
        user = result.scalar_one_or_none()
        await async_session.execute(delete(Like).where(Like.tweet_id == id, Like.user_id==user.id))
        await async_session.commit()
        return ResultModel(result=True)


    except Exception as er:
        print("!" * 100)
        print("DELETE tweets LIKE")
        print(ErrorModel(
            result=False,
            error_type=str(type(er).__name__),
            error_message=str(er),
        ))
        return {
            "result": False,
            "error_type": str(type(er).__name__),
            "error_message": str(er),
        }

#
@app.get("/api/tweets", response_model=ResultTweetsModel | ErrorModel)
async def get_user_tweets(api_key: str = Depends(get_client_token), async_session: AsyncSession = Depends(get_session)):
    """
    Получает твиты текущего пользователя и информацию о его подписчиках.
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
                select(User.id,
                       User.name)
                       .join(Like, Like.user_id == User.id)
                       .where(Like.tweet_id == int(tweet[0])))
            likes = result.fetchall()
            tweets_output.append({
                    "id": int(tweet[0]),
                    "content": tweet[1],
                    "attachments": [f"/api/medias/{int(tweet[2])}"] if tweet.media_id else [],
                    "author":{
                            "id": int(tweet[3]),
                            "name": tweet[4]
                        },
                    "likes":[
                        {
                            "user_id":liker[0],
                            "name":liker[1]
                            } for liker in likes]
                        })
        return ResultTweetsModel(result=True, tweets=tweets_output)

    except Exception as er:
        return ErrorModel(
                result=False,
                error_type=str(type(er).__name__),
                error_message=str(er),
            )

@app.get("/api/users/me", response_model=ResultUserInfoModelOut|ErrorModel)
async def get_current_user(api_key: str = Depends(get_client_token), async_session: AsyncSession = Depends(get_session)):
    try:
        result = await async_session.execute(
            select(User).where(User.api_key == api_key)
        )
        user = result.scalar_one_or_none()
        followers = await get_followers(user.id, async_session)
        following = await get_following(user.id, async_session)
        user_info = UserInfoModel(
            id=user.id,
            name=user.name,
            followers=followers,
            following=following
        )
        return ResultUserInfoModelOut(result = True, user = user_info)

    except Exception as er:
        print("!"*100)
        print("GET user/me")
        print(ErrorModel(
            result=False,
            error_type=str(type(er).__name__),
            error_message=str(er),
        ))
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
        account_result = await async_session.execute(
                     select(User)
                     .where(User.id == id)
               )
        user = account_result.scalar_one_or_none()
        followers = await get_followers(id, async_session)
        following = await get_following(id, async_session)
        user_info = UserInfoModel(
            id=user.id,
            name=user.name,
            followers=followers,
            following=following
        )
        return ResultUserInfoModelOut(result=True, user=user_info)
    except Exception as er:
        return ErrorModel(
            result = False,
            error_type = str(type(er).__name__),
            error_message = str(er),
        )


@app.delete("/api/users/{id}/follow", response_model=ErrorModel|ResultModel)
async def unfollow(id: int, api_key: str = Depends(get_client_token), async_session: AsyncSession = Depends(get_session)):
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
                ))
        result = unfollower.scalar_one_or_none()
        await async_session.delete(result)
        await async_session.commit()
        return ResultModel(result=True)

    except Exception as er:
        print(ErrorModel(
            result=False,
            error_type=str(type(er).__name__),
            error_message=str(er),
        ))
        return ErrorModel(
            result=False,
            error_type=str(type(er).__name__),
            error_message=str(er),
        )


@app.post("/api/users/{id}/follow")
async def follow(id: int, api_key: str = Depends(get_client_token), async_session: AsyncSession = Depends(get_session)):
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
        return ResultModel(result = True)

    except Exception as er:
        return ErrorModel(
            result=False,
            error_type=str(type(er).__name__),
            error_message=str(er),
        )
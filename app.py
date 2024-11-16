from os import write

import uvicorn
from database.database import engine, session, Base
from database.models import User, Tweet, Like, Media, Follower
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

# @app.lifespan()
# async def lifespan(app: FastAPI):
#     """
#     функция выполняет код при начале работы с приложением
#     (инициализация бд)
#     и после yield функуия выполняет действия после закрытия приложения
#     """
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)
#     async with session() as sync_ses:
#         user_test = User()
#         user_test.api_key = TEST_NAME
#         user_test.name = TEST_NAME + " Frank"
#         api_key_now = TEST_NAME
#
#     yield
#
#     async with session() as sync_ses:
#         query = sync_ses.delete(User).were(User.api_key==TEST_NAME)
#         sync_ses.execute(query)
#     await session.close()
#     await engine.dispose()


@app.post("/api/tweets")
async def tweets(tweet: TweetCreate, api_key: str = Depends(get_client_token)):
    """
        Запросом на этот endpoint пользователь будет создавать новый твит.
        Бэкенд будет его валидировать и сохранять в базу.
        :param api_key:str Получение ключа (Имитация сессии)
        :return:dict  В ответ должен вернуться id созданного твита.
    """
    try:
        async with session() as as_session:
            new_tweet = Tweet(tweet_data=tweet.tweet_data, tweet_media_ids=tweet.tweet_media_ids)
            as_session.add(new_tweet)
        result = {
                "result": True,
                "tweet_id": new_tweet.id
                 }
        return result
    except Exception as er:
        return {
            "result": False,
            "error_type": str(type(er).__name__),  # Получаем название типа ошибки
            "error_message": str(er)  # Получаем сообщение об ошибке
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
        async with session() as async_ses:
            last_id = await async_ses.execute(select(Media.id).order_by(Media.id.desc()).limit(1)).scalar_one_or_none()

        if last_id is not None:
            filename = f"{api_key + file.filename + str(last_id + 1)}"

        else:
            filename = f"{api_key + file.filename + str(last_id)}1"

        async with open(PATH_IMAGE+filename, "wb") as file:
            await file.write

        async with session() as async_session:
            safe_image = Media(filename=filename)
            last_id = await async_ses.execute(select(Media.id).order_by(Media.id.desc()).limit(1)).scalar_one_or_none()
            await async_session.add(safe_image)
        result = {
                 "result": True,
                 "media_id": last_id
                 }
        return result

    except Exception as er:
        return {
            "result": False,
            "error_type": str(type(er).__name__),  # Получаем название типа ошибки
            "error_message": str(er)  # Получаем сообщение об ошибке
        }


@app.delete("/api/tweets/<id>")
async def delete_tweet(id: int, api_key: str = Depends(get_client_token)):
    """
        Пользователь может Удалить Твит.
        :param id:int Получение id Пользователя
        :param api_key:str Получение ключа (Имитация сессии)
        :return:dict  В ответ должно вернуться сообщение о статусе операции.
        """
    try:
        pass

    except Exception as er:
        return {
            "result": False,
            "error_type": str(type(er).__name__),  # Получаем название типа ошибки
            "error_message": str(er)  # Получаем сообщение об ошибке
        }


@app.post("/api/tweets/<id>/likes")
async def like(id: int, api_key: str = Depends(get_client_token)):
    """
        Пользователь может поставить отметку «Нравится» на твит.
        :param id:int Получение id Пользователя
        :param api_key:str Получение ключа (Имитация сессии)
        :return:dict  В ответ должно вернуться сообщение о статусе операции.
        """
    try:
        pass

    except Exception as er:
        return {
            "result": False,
            "error_type": str(type(er).__name__),  # Получаем название типа ошибки
            "error_message": str(er)  # Получаем сообщение об ошибке
        }

@app.delete("/api/tweets/<id>/likes")
async def delete_like(id: int, api_key: str = Depends(get_client_token)):
    """
        Пользователь может убрать отметку «Нравится» с твита.
        :param id:int Получение id Пользователя
        :param api_key:str Получение ключа (Имитация сессии)
        :return:dict  В ответ должно вернуться сообщение о статусе операции.
    """
    try:
        pass

    except Exception as er:
        return {
            "result": False,
            "error_type": str(type(er).__name__),  # Получаем название типа ошибки
            "error_message": str(er)  # Получаем сообщение об ошибке
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
        pass

    except Exception as er:
        return {
            "result": False,
            "error_type": str(type(er).__name__),  # Получаем название типа ошибки
            "error_message": str(er)  # Получаем сообщение об ошибке
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
        pass

    except Exception as er:
        return {
            "result": False,
            "error_type": str(type(er).__name__),  # Получаем название типа ошибки
            "error_message": str(er)  # Получаем сообщение об ошибке
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
        pass

    except Exception as er:
        return {
            "result": False,
            "error_type": str(type(er).__name__),  # Получаем название типа ошибки
            "error_message": str(er)  # Получаем сообщение об ошибке
        }


@app.get("/api/users/me")
async def my_account(api_key: str = Depends(get_client_token)):
    """
        Пользователь может получить информацию о своём профиле
        :param api_key:str Получение ключа (Имитация сессии)
        :return:dict
    """
    try:
        pass

    except Exception as er:
        return {
            "result": False,
            "error_type": str(type(er).__name__),  # Получаем название типа ошибки
            "error_message": str(er)  # Получаем сообщение об ошибке
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
        async with session() as sync_ses:
            query = sync_ses.query(User).filter(User.id == id)
            result_user = await sync_ses.execute(query).fetchone()

            if result_user is None:
                raise
            result = {
                "result": True,
                "user": {
                    "id": result_user.id,
                    "name": result_user.name,
                    "followers": [{"id": follower.id, "name": follower.name} for follower in result_user.followers],
                    "following": [{"id": following.id, "name": following.name} for following in result_user.following]
                }
            }
        return result

    except Exception as er:
        return {
            "result": False,
            "error_type": str(type(er).__name__),  # Получаем название типа ошибки
            "error_message": str(er)  # Получаем сообщение об ошибке
        }


if __name__ == "__main__":
    uvicorn.run("app:app")
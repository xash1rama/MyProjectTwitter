from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class ResultModel(BaseModel):
    """Возвращает информацию о статусе операции"""

    model_config = ConfigDict()  # Установите параметры конфигурации, если нужно
    result: bool


class ErrorModel(ResultModel):
    """Возвращает информацию об ошибке в операции"""

    error_type: str
    error_message: str


class TweetCreate(BaseModel):
    """Получение информации для создания твита"""

    tweet_data: str  # Текст твита
    tweet_media_ids: Optional[List[int]]  # Убедитесь, что тип данных корректен


class UserModel(BaseModel):
    """Модель автора для возвращения пользователю"""

    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)  # Обновленный конфиг


class LikeModel(BaseModel):
    """Модель лайка"""

    user_id: int
    name: str


class TweetModel(BaseModel):
    """Модель твита"""

    id: int
    content: str
    attachments: List[str]
    author: UserModel
    likes: Optional[List[LikeModel]] = []

    model_config = ConfigDict(from_attributes=True)  # Обновленный конфиг


class TweetAdd(ResultModel):
    """Возвращает готовый твит"""

    tweet_id: int


class MediaModel(ResultModel):
    """Возвращает модель созданного медиа"""

    media_id: int

    model_config = ConfigDict(from_attributes=True)  # Обновленный конфиг


class GetTweets(ResultModel):
    """Возвращает список твитов"""

    tweets: List[TweetModel]


class UserInfoModel(UserModel):
    """Модель пользователя с подписчиками и подписками"""

    followers: Optional[List[UserModel]] = []
    following: Optional[List[UserModel]] = []


class ResultUserInfoModelOut(ResultModel):
    """Возвращает полную информацию о пользователе"""

    user: UserInfoModel


class ResultTweetsModel(ResultModel):
    """Возвращает полную информацию о твитах"""

    tweets: List[TweetModel]

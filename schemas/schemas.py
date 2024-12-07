from pydantic import BaseModel
from typing import Optional, List



class ResultModel(BaseModel):
    """Возвращает информацию о статусе операции"""
    result: bool

class ErrorModel(ResultModel):
    """Возвращает информацию о статусе операции"""
    error_type: str
    error_message: str

class TweetCreate(BaseModel):
    """Полученик информацию для создания твите"""
    tweet_data: str  # Текст твита
    tweet_media_ids: list[int] | None

class UserModel(BaseModel):
    """Модель автора для возвращения пользователю"""
    id: int
    name: str

    class Config:
        from_attributes = True

class LikeModel(BaseModel):
    user_id: int
    name: str

class TweetModel(BaseModel):
    id: int
    content: str
    attachments: List[str]
    author: UserModel
    likes: Optional[List[LikeModel]] = []
    class Config:
        from_attributes = True

class TweetAdd(ResultModel):
    """Возвращает готовый твит"""
    tweet_id: int

class MediaModel(ResultModel):
    """Возвращает модель созданного медиа"""
    media_id:int
    class Config:
        from_attributes = True


class GetTweets(ResultModel):
    """Возвращает твиты"""
    tweets: List[TweetModel]

class UserModel(BaseModel):
    """Модель автора для возвращения пользователю"""
    id: int
    name: str

    class Config:
        from_attributes = True

class UserInfoModel(UserModel):
    """Модель пользователя для возвращения ему"""
    followers: Optional[List[UserModel]]=[]
    following: Optional[List[UserModel]]=[]

class ResultUserInfoModelOut(ResultModel):
    """Возвращает полную информацию о пользователе"""
    user: UserInfoModel

class ResultTweetsModel(ResultModel):
    tweets: List[TweetModel]

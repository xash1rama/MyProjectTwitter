from pydantic import BaseModel
from typing import Optional, List


class TweetCreate(BaseModel):
    tweet_data: str  # Текст твита
    tweet_media_ids: Optional[List[int]] = None  # Опциональный список ID медиафайлов

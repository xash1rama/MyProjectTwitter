from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, ARRAY, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+asyncpg://admin:admin@postgres_container:5432/tweet_db"
engine = create_async_engine(DATABASE_URL, echo=True)
session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    name: str = Column(String, nullable=False)
    api_key: str = Column(String, nullable=False)
    followers = relationship("Follower",
                             back_populates="user_following",
                             foreign_keys="[Follower.following_id]",
                             lazy="select",
                             cascade="all"
                             )
    following = relationship("Follower",
        back_populates="user_follower",
                             foreign_keys="[Follower.follower_id]",
                             lazy="select",
                             cascade="all"
                             )
    tweet = relationship(
        "Tweet", back_populates="user_tweet", lazy="select", cascade="all"
    )
    likes = relationship("Like", back_populates="user_like", cascade="all")

    def to_json(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Tweet(Base):
    __tablename__ = "tweets"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    user_id: int = Column(Integer, ForeignKey("users.id"))
    tweet_data: str = Column(String, nullable=False)
    tweet_media_ids: list = Column(ARRAY(Integer), nullable=True)
    time: datetime = Column(DateTime, default=datetime.now())
    user_tweet = relationship("User", back_populates="tweet")
    likes = relationship("Like", back_populates="tweet_like", cascade="all")
    tweet_media = relationship(
        "Media", back_populates="media_tweet", lazy="select", cascade="all"
    )

    def to_json(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Like(Base):
    __tablename__ = "likes"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    user_id: int = Column(Integer, ForeignKey("users.id"))
    tweet_id: int = Column(Integer, ForeignKey("tweets.id"))
    user_like = relationship("User", back_populates="likes")
    tweet_like = relationship("Tweet", back_populates="likes")

    def to_json(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Follower(Base):
    __tablename__ = "followers"

    follower_id: int = Column(Integer, ForeignKey("users.id"), primary_key=True)
    following_id: int = Column(Integer, ForeignKey("users.id"), primary_key=True)
    user_follower = relationship("User", foreign_keys=[follower_id], back_populates="following")
    user_following = relationship("User", foreign_keys=[following_id], back_populates="followers")
    time: datetime = Column(DateTime, default=datetime.now())

    def to_json(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Media(Base):
    __tablename__ = "medias"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    filename: str = Column(String, nullable=False)
    tweet_id: int = Column(Integer, ForeignKey("tweets.id"))
    media_tweet = relationship("Tweet", back_populates="tweet_media")

    def to_json(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

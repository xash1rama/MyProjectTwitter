from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
import os
from dotenv import load_dotenv

load_dotenv("../.env")


DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

DB_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@postgresql_container:5432/{DB_NAME}"


def init_db(db_url):
    engine = create_async_engine(db_url, echo=True)
    session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return engine, session


engine, session = init_db(DB_URL)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    api_key = Column(String, nullable=False)
    followers = relationship(
        "Follower",
        back_populates="user_following",
        foreign_keys="[Follower.following_id]",
        lazy="select",
        cascade="all",
    )
    following = relationship(
        "Follower",
        back_populates="user_follower",
        foreign_keys="[Follower.follower_id]",
        lazy="select",
        cascade="all",
    )
    tweets = relationship(
        "Tweet", back_populates="user_tweet", lazy="select", cascade="all"
    )
    likes = relationship("Like", back_populates="user_like", lazy="select")

    def to_json(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Tweet(Base):
    __tablename__ = "tweets"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    tweet_data = Column(String, nullable=False)
    time = Column(DateTime, default=datetime.utcnow)
    user_tweet = relationship("User", back_populates="tweets")
    likes = relationship(
        "Like", back_populates="tweet_like", cascade="all, delete-orphan"
    )
    medias = relationship("Media", back_populates="tweet", cascade="all, delete-orphan")

    def to_json(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    @classmethod
    async def get_last_tweet(cls, async_session: AsyncSession):
        result = await async_session.execute(
            select(cls).order_by(cls.time.desc()).limit(1)
        )
        return result.scalar_one_or_none()


class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    tweet_id = Column(Integer, ForeignKey("tweets.id"))
    user_like = relationship("User", back_populates="likes")
    tweet_like = relationship("Tweet", back_populates="likes")

    def to_json(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Follower(Base):
    __tablename__ = "followers"

    follower_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    following_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    user_follower = relationship(
        "User", foreign_keys=[follower_id], back_populates="following"
    )
    user_following = relationship(
        "User", foreign_keys=[following_id], back_populates="followers"
    )
    time = Column(DateTime, default=datetime.utcnow)

    def to_json(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Media(Base):
    __tablename__ = "medias"

    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    tweet_id = Column(Integer, ForeignKey("tweets.id"))
    tweet = relationship("Tweet", back_populates="medias")

    def to_json(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

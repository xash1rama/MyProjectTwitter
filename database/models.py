from datetime import datetime
from sqlalchemy import Column, Integer, String, LargeBinary, ForeignKey, ARRAY, DATETIME
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

DATABASE_URL = "postgresql+asyncpg://username:password@localhost/dbname"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
session = async_session()
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    name: str = Column(String, nullable=False)
    api_key: str = Column(String, nullable=False)
    follower = relationship(
        "Follower", back_populates="user_follower", lazy="select", cascade="all"
    )
    following = relationship(
        "Follower", back_populates="user_following", lazy="select", cascade="all"
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
    time: datetime = Column(DATETIME, default=datetime.now())
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
    users_follower = relationship("User", back_populates="follower")
    users_following = relationship("User", back_populates="following")
    time: datetime = Column(DATETIME, default=datetime.now())

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

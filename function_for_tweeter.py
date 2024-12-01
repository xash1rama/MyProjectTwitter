from database.models import session, User
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import APIKeyHeader
from sqlalchemy.future import select
from fastapi import Depends, HTTPException
from database.models import Follower

header_api_key = APIKeyHeader(name="api-key")


async def get_session() -> AsyncSession:
    async with session() as async_session:
        yield async_session


async def get_client_token(api_key: str = Depends(header_api_key),
                           async_session: AsyncSession = Depends(get_session)):
    result = await async_session.execute(select(User.api_key))
    valid_api_keys = result.scalars().all()
    if api_key not in valid_api_keys:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

async def get_following(id:int, async_session: AsyncSession = Depends(get_session)):
    following = await async_session.execute(select(Follower.following_id).where(Follower.follower_id==id))
    result = following.scalars().all()
    if result:
        return [{"id":follower.id, "name":follower.name} for follower in result]
    return []

async def get_followers(id:int, async_session: AsyncSession = Depends(get_session)):
    following = await async_session.execute(select(Follower.follower_id).where(Follower.following_id==id))
    result = following.scalars().all()
    if result:
        return [{"id":follower.id, "name":follower.name} for follower in result]
    return []


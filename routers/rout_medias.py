from aiohttp.abc import HTTPException
from fastapi import APIRouter, Depends, UploadFile, File, Response
from database.models import Media, User, Tweet
from schemas.schemas import MediaModel, ErrorModel
from sqlalchemy.future import select
from config.function_for_tweeter import get_client_token, get_session
from sqlalchemy.ext.asyncio import AsyncSession
import aiofiles
from config.conf_app import PATH_IMAGE
import os

router = APIRouter(tags=["media"])


@router.post("/api/medias", response_model=MediaModel | ErrorModel)
async def upload_media(
    file: UploadFile = File(...),
    api_key: str = Depends(get_client_token),
    async_session: AsyncSession = Depends(get_session),
):
    """
    Endpoint для загрузки файлов из твита. Загрузка происходит через отправку формы.
    """
    try:
        result = await async_session.execute(
            select(User).where(User.api_key == api_key)
        )
        id_user = result.scalar_one_or_none()
        last_id_result = await async_session.execute(
            select(Tweet.id)
            .where(Tweet.user_id == id_user.id)
            .order_by(Tweet.id.desc())
            .limit(1)
        )
        last_id = last_id_result.scalar_one_or_none()
        contents = await file.read()
        os.makedirs(PATH_IMAGE, exist_ok=True)

        file_name = (
            "user_id:" + str(id_user.id) + "tweet_id:" + str(last_id) + file.filename
        )

        file_path = os.path.join(PATH_IMAGE, file_name)
        async with aiofiles.open(file_path, "wb") as file_save:
            await file_save.write(contents)

        safe_image = Media(filename=file_name, tweet_id=last_id)
        async_session.add(safe_image)
        await async_session.commit()
        await async_session.refresh(safe_image)

        return MediaModel(result=True, media_id=safe_image.id)

    except Exception as er:
        print("!" * 100)
        print("POST medias")
        print(
            ErrorModel(
                result=False,
                error_type=str(type(er).__name__),
                error_message=str(er),
            )
        )
        return ErrorModel(
            result=False,
            error_type=str(type(er).__name__),
            error_message=str(er),
        )


@router.get("/api/medias/{id}")
async def get_image(id: int, async_session: AsyncSession = Depends(get_session)):
    """
    Endpoint для отдачи изображения на страницу твитов
    """
    try:
        result = await async_session.execute(
            select(Media.filename).where(Media.id == id)
        )
        image_filename = result.scalar_one_or_none()
        if not image_filename:
            raise HTTPException(status_code=404, detail="Image not found")
        file_path = os.path.join(PATH_IMAGE, image_filename)
        if not os.path.isfile(file_path):
            raise HTTPException(status_code=404, detail="Image file does not exist")
        async with aiofiles.open(file_path, mode="rb") as file:
            image_bytes = await file.read()
        return Response(content=image_bytes, media_type="image/jpeg")

    except Exception as er:
        return ErrorModel(
            result=False,
            error_type=str(type(er).__name__),
            error_message=str(er),
        )

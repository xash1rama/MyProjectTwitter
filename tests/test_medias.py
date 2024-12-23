import pytest
from .conftest import client, test_db


@pytest.mark.asyncio
async def test_upload_and_view_media(client):
    """
    Сначала происходит загрузка файла в бд
    Потом происходит создание твита
    Потом тестовая подгрузка картинки
    В конце удаление твита
    """
    api_key = "test"
    file_path = "tests/test_image.jpg"
    with open(file_path, "rb") as f:
        response = await client.post(
            "/api/medias",
            headers={"api-key": api_key},
            files={"file": ("test_image.jpg", f, "image/jpeg")},
        )
    data = response.json()
    tweet_data = {"tweet_data": "Тестовый твит", "tweet_media_ids": [data["media_id"]]}
    res = await client.post(
        "/api/tweets", json=tweet_data, headers={"api-key": api_key}
    )

    assert response.status_code == 200
    assert response.json()["result"] is True

    view_media = await client.get(f"/api/medias/{data['media_id']}")
    assert view_media.status_code == 200

    datas = res.json()
    tweet_id = datas["tweet_id"]
    res = await client.delete(
        "/api/tweets/" + str(tweet_id), headers={"api-key": api_key}
    )
    assert res.status_code == 200
    assert res.json()["result"] is True


@pytest.mark.asyncio
async def test_get_image_not_found(client):
    """Попытка загрущить несуществующее медиа"""
    response = await client.get("/api/medias/999")
    assert response.json()["result"] == False

import pytest
from .conftest import client, test_db


@pytest.mark.asyncio
async def test_get_user_tweets(client, test_db):
    """Тест получения твитов первого пользоваителя"""
    response = await client.get("/api/tweets", headers={"api-key": "test"})
    assert response.status_code == 200
    assert response.json()["result"] == True


@pytest.mark.asyncio
async def test_get_user_tweets_2(client, test_db):
    """Тест получения твитов второго пользоваителя"""

    response = await client.get("/api/tweets", headers={"api-key": "test_2"})
    assert response.status_code == 200
    assert response.json()["result"] == True


@pytest.mark.asyncio
async def test_create_like_delete_tweet(client, test_db):
    """Тест создания, лайка и удаления твита у первого пользователя"""

    api_key = "test"
    tweet_data = {"tweet_data": "Тестовый твит", "tweet_media_ids": []}
    response = await client.post(
        "/api/tweets", json=tweet_data, headers={"api-key": api_key}
    )
    data = response.json()
    tweet_1 = data["tweet_id"]
    assert response.status_code == 200
    assert data["result"] is True
    assert "tweet_id" in data

    response = await client.post(
        f"/api/tweets/{str(tweet_1)}/likes", headers={"api-key": api_key}
    )
    print(response.json())
    assert response.status_code == 200
    assert response.json()["result"] is True

    api_key = "test"
    response = await client.delete(
        f"/api/tweets/{str(tweet_1)}/likes", headers={"api-key": api_key}
    )
    assert response.status_code == 200
    assert response.json()["result"] is True

    response = await client.delete(
        f"/api/tweets/{str(tweet_1)}", headers={"api-key": api_key}
    )
    assert response.status_code == 200
    assert response.json()["result"] is True


@pytest.mark.asyncio
async def test_create_like_delete_tweet_2(client, test_db):
    """Тест создания, лайка и удаления твита у второго пользователя"""

    api_key = "test_2"
    tweet_data = {"tweet_data": "Тестовый твит", "tweet_media_ids": []}
    response = await client.post(
        "/api/tweets", json=tweet_data, headers={"api-key": api_key}
    )
    data = response.json()
    tweet_2 = data["tweet_id"]
    assert response.status_code == 200
    assert data["result"] is True
    assert "tweet_id" in data

    response = await client.post(
        f"/api/tweets/{str(tweet_2)}/likes", headers={"api-key": api_key}
    )
    assert response.status_code == 200
    assert response.json()["result"] is True

    response = await client.delete(
        f"/api/tweets/{str(tweet_2)}/likes", headers={"api-key": api_key}
    )
    assert response.status_code == 200
    assert response.json()["result"] is True

    response = await client.delete(
        f"/api/tweets/{str(tweet_2)}", headers={"api-key": api_key}
    )
    assert response.status_code == 200
    assert response.json()["result"] is True


@pytest.mark.asyncio
async def test_create_tweet_with_invalid_api_key(client, test_db):
    """Тест создания твита с невалидным api-key"""

    api_key = "invalid_api_key"
    tweet_data = {"tweet_data": "Тестовый твит", "tweet_media_ids": []}

    response = await client.post(
        "/api/tweets", json=tweet_data, headers={"api-key": api_key}
    )

    data = response.json()
    assert response.status_code == 403
    assert data["detail"] == "Invalid API key"


@pytest.mark.asyncio
async def test_like_invalid_tweet(client, test_db):
    """Тест создания лайка несуществующего твита"""

    api_key = "test_2"
    response = await client.post("/api/tweets/1111/likes", headers={"api-key": api_key})

    assert response.status_code == 200
    assert response.json()["result"] is False


@pytest.mark.asyncio
async def test_delete_tweet_not_found(client, test_db):
    """Тест удаления твита у несуществующего твита"""

    api_key = "test"
    non_existent_tweet_id = 99999
    response = await client.delete(
        f"/api/tweets/{non_existent_tweet_id}", headers={"api-key": api_key}
    )

    assert response.status_code == 200
    assert response.json()["result"] is False


@pytest.mark.asyncio
async def test_delete_tweet_invalid_api_key(client, test_db):
    """Тест удаления твита с невалидным api-key"""

    response = await client.delete(
        f"/api/tweets/1", headers={"api-key": "invalid_api_key"}
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid API key"

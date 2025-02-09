import pytest
from aiogram import types
from unittest.mock import AsyncMock, patch

from main import handle_start, handle_weather, get_coords
from weather_getter.exceptions import CantGetCoordinates, ApiServiceError

@pytest.mark.asyncio
async def test_handle_start():
    message_mock = AsyncMock(text='/start', from_user=types.User(
        id=123,
        first_name="Test",
        last_name="User",
        username="testuser",
        is_bot=False
    ))
    await handle_start(message=message_mock)
    message_mock.answer.assert_called_once()

    assert "Приветствую" in message_mock.answer.call_args[1]['text']


@pytest.mark.asyncio
async def test_handle_weather_city_not_found():
    message_mock = AsyncMock(text=".........", chat=types.Chat(id=12345, type="private"))
    message_mock.bot.send_chat_action = AsyncMock()
    message_mock.answer = AsyncMock()

    with patch('main.r.get', return_value=None), \
        patch('main.get_coords', side_effect=CantGetCoordinates):
        await handle_weather(message_mock)

    message_mock.answer.assert_called_once_with('Город не найден.')


@pytest.mark.asyncio
async def test_handle_weather_api_service_error():
    message_mock = AsyncMock(text="................", chat=types.Chat(id=12345, type="private"))
    message_mock.bot.send_chat_action = AsyncMock()
    message_mock.answer = AsyncMock()

    with patch('main.r.get', return_value=None), \
        patch('main.get_coords', return_value=(55.7558, 37.6173)), \
        patch('main.get_weather', side_effect=ApiServiceError):
        await handle_weather(message_mock)

    message_mock.answer.assert_called_once_with('Проблема с подключением к сервису погоды.')
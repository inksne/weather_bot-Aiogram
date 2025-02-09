from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.utils import markdown
from aiogram.enums.parse_mode import ParseMode
from aiogram.enums.chat_action import ChatAction
from aiogram.utils.chat_action import ChatActionSender

from fastapi import FastAPI
import uvicorn

from redis import Redis

from config import BOT_TOKEN, USE_ROUNDED_COORDS, configure_logging
from weather_getter.weather_api_service import get_weather
from weather_getter.weather_formatter import format_weather
from weather_getter.exceptions import CantGetCoordinates, ApiServiceError

from geopy.geocoders import Nominatim

import asyncio
import logging
from typing import NamedTuple


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

app = FastAPI()

configure_logging()
logger = logging.getLogger(__name__)

r = Redis(host='redis', port=6379, db=0)


class Coordinates(NamedTuple):
    latitude: float
    longitude: float


async def get_coords(location: str):
    try:
        loc = Nominatim(user_agent="GetLoc")
        getLoc = await asyncio.to_thread(loc.geocode, location)
        if getLoc is None:
            raise CantGetCoordinates
        latitude = getLoc.latitude
        longitude = getLoc.longitude
        if USE_ROUNDED_COORDS:
            latitude, longitude = map(lambda c: round(c, 1), [latitude, longitude])
        return Coordinates(latitude=latitude, longitude=longitude)
    except CantGetCoordinates:
        raise ApiServiceError


@dp.message(CommandStart())
async def handle_start(message: types.Message):
    await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    text = markdown.text(
        f'Приветствую, {markdown.hbold(message.from_user.full_name)}!',
        markdown.text('Я -', markdown.hbold('простой бот для получения погоды')),
        markdown.text(
            f'Давайте устроим простой {markdown.hunderline('обмен')}: вы мне название города, а я вам погоду в нем, окей?'
        ),
        sep='\n'
    )
    await message.answer(text=text, parse_mode=ParseMode.HTML)


@dp.message()
async def handle_weather(message: types.Message):
    if message.text:
        async with ChatActionSender.typing(chat_id=message.chat.id, bot=message.bot):
            try:
                location = message.text.lower()
                weather_from_redis = r.get(f'weather:{location}')

                if weather_from_redis:
                    logger.info(f'данные по {location} найдены в редисе')
                    formatted_weather = weather_from_redis.decode('utf-8')

                    text = markdown.text(
                        markdown.hbold(message.text),
                        formatted_weather,
                        sep='\n'
                    )
                    await message.answer(text=text, parse_mode=ParseMode.HTML)
                else:
                    logger.info(f'данные по {location} не найдены в редисе')

                    coords = await get_coords(location)
                    weather = await get_weather(coords)
                    formatted_weather = format_weather(weather)
                    
                    r.set(f'weather:{location}', formatted_weather, ex=1800)

                    text = markdown.text(
                        markdown.hbold(message.text),
                        formatted_weather,
                        sep='\n'
                    )
                    await message.answer(text=text, parse_mode=ParseMode.HTML)
            except CantGetCoordinates as e:
                logger.error(e)
                await message.answer('Город не найден.')
            except ApiServiceError as e:
                logger.error(e)
                await message.answer('Проблема с подключением к сервису погоды.')
            except Exception as e:
                logger.error(e)
                await message.answer('Проблема с получением погоды.')
    else:
        text = markdown.text(f'Пожалуйста, отправьте {markdown.hbold('текстовое')} сообщение.')
        await message.answer(text=text, parse_mode=ParseMode.HTML)


async def start_bot():
    configure_logging()
    await dp.start_polling(bot)


async def main():
    uvicorn_config = uvicorn.Config("main:app", host="0.0.0.0", port=10000)
    server = uvicorn.Server(uvicorn_config)
    
    await asyncio.gather(
        start_bot(),
        server.serve()
    )


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        exit(0)
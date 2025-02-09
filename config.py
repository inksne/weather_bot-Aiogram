import os
from dotenv import load_dotenv
import logging

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_TOKEN = os.environ.get("API_TOKEN")

USE_ROUNDED_COORDS = True
GISMETEO_URL = (
    "https://api.gismeteo.net/v2/weather/current/?latitude={latitude}&longitude={longitude}&token={API_TOKEN}"
)


def configure_logging(level: int = logging.INFO):
    logging.basicConfig(
        level=level,
        datefmt="%Y-%m-%d %H:%M:%S",
        format="[%(asctime)s.%(msecs)03d] %(funcName)20s %(module)s:%(lineno)d %(levelname)-8s - %(message)s"
    )
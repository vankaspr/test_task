import random
import string
import httpx
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


app = FastAPI()


url_store = {}


class URLRequest(BaseModel):
    url: HttpUrl


def generate_short_id(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


async def check_url(url: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.head(url, follow_redirects=True)
            logger.debug(f"Проверка URL: {url} → {response.status_code}")
            return response.status_code < 400
    except httpx.RequestError as e:
        logger.warning(f"Ошибка при проверке URL {url}: {e}")
        return False


# POST
@app.post("/", status_code=201)
async def shorten_url(request: URLRequest):
    url = request.url
    logger.info(f"Запрос на сокращение URL: {url}")
    if not await check_url(str(url)):
        logger.warning(f"URL недоступен: {url}")
        raise HTTPException(status_code=400, detail="url is not accessible")

    short_id = generate_short_id()
    url_store[short_id] = str(url)
    logger.info(f"URL сохранён: {url} -> {short_id}")
    return {"short_url_id": short_id}


# GET
@app.get("/{short_id}")
async def redirect_url(short_id: str):
    original_url = url_store.get(short_id)
    if not original_url:
        logger.error(f"Переход по несуществующей ссылке: {short_id}")
        raise HTTPException(status_code=404, detail="short url not found")
    logger.info(f"Перенаправление: {short_id} -> {original_url}")
    return RedirectResponse(original_url, status_code=307)



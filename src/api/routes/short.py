from aiohttp import web
from prisma.errors import UniqueViolationError

from src.utils.database import database

from ..utils.short import generate_random_string


async def shorten(req: web.Request):
    body = await req.json()

    text = body.get("text")
    url = body.get("url")

    if not text:
        text = generate_random_string(4)

    try:
        data = await database.url.create(
            data={"text": text, "destination": url},
        )
    except UniqueViolationError:
        return web.json_response(
            {
                "success": False,
                "error": "Duplicate URL detected",
            }
        )

    return web.json_response(
        {
            "success": True,
            "url": data.destination,
            "text": text,
        }
    )


async def redirect(req: web.Request):
    text = req.match_info.get("text")

    data = await database.url.find_first(where={"text": text})
    if not data:
        return web.HTTPNotFound()

    return web.HTTPFound(data.destination)

from aiohttp import web
from src.api.utils.xbox import get_profile, send_message
from src.utils.database import database


async def profile(request: web.Request):
    settings = await database.settings.find_first()
    authorization = settings.xapi

    username = request.match_info["username"]

    data = await get_profile(authorization, username)
    return web.json_response(data)


async def message(request: web.Request):
    settings = await database.settings.find_first()
    authorization = settings.xapi

    body = await request.json()
    message = body.get("message")
    username = request.match_info["username"]

    data = await send_message(authorization, username, message)
    return web.json_response(data)

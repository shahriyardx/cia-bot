from aiohttp import web
from src.api.utils.psn import get_profile, send_message
from src.utils.database import database


async def profile(request: web.Request):
    settings = await database.settings.find_first()
    authorization = settings.npsso

    username = request.match_info["username"]

    data = get_profile(authorization, username)
    return web.json_response(data)


async def message(request: web.Request):
    settings = await database.settings.find_first()
    authorization = settings.npsso

    body = await request.json()
    username = request.match_info["username"]
    message = body.get("message")

    data = send_message(authorization, username, message)
    return web.json_response(data)

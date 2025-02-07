from aiohttp import web

from src.api.utils.console import get_xapi_token
from src.api.utils.xbox import get_profile, send_friend_request, send_message
from src.utils.database import database


async def profile(request: web.Request):
    authorization = await get_xapi_token()
    username = request.match_info["username"]

    data = await get_profile(authorization, username)
    return web.json_response(data)


async def message(request: web.Request):
    authorization = await get_xapi_token()

    body = await request.json()
    message = body.get("message")
    username = request.match_info["username"]

    data = await send_message(authorization, username, message)
    return web.json_response(data)


async def friend_request(request: web.Request):
    authorization = await get_xapi_token()
    username = request.match_info["username"]

    data = await send_friend_request(authorization, username)
    return web.json_response(data)

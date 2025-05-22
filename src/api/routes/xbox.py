from aiohttp import web

from src.api.utils.console import get_xapi_token
from src.api.utils.xbox import (
    get_profile,
    get_profile_by_id,
    send_friend_request,
    send_message,
)


async def profile(request: web.Request):
    authorization = await get_xapi_token()
    username = request.match_info["username"]

    data = await get_profile(authorization, username)
    return web.json_response(data)


async def profile_by_id(request: web.Request):
    authorization = await get_xapi_token()
    account_id = request.match_info["account_id"]

    data = await get_profile_by_id(authorization, account_id)
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

from aiohttp import web

from src.api.utils.console import get_npsso
from src.api.utils.psn import get_profile, get_profile_by_id, send_message


async def profile(request: web.Request):
    authorization = await get_npsso()
    username = request.match_info["username"]

    data = get_profile(authorization, username)
    return web.json_response(data)


async def profile_by_id(request: web.Request):
    authorization = await get_npsso()
    account_id = request.match_info["account_id"]

    data = get_profile_by_id(authorization, account_id)
    return web.json_response(data)


async def message(request: web.Request):
    authorization = await get_npsso()
    body = await request.json()
    username = request.match_info["username"]
    message_content = body.get("message")

    data = send_message(authorization, username, message_content)
    return web.json_response(data)

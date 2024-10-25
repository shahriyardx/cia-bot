import asyncio

import hikari
from aiohttp import web

from src.utils import get_support_server
from src.utils.ticket import start_ticket


async def index(_):
    return web.json_response({"hello": "world"})


async def add_to_server(request: web.Request):
    body = await request.json()

    print(request.headers.keys())
    access_token = request.headers.get("access_token")
    user_id = body.get("user_id")

    print(access_token, user_id)
    guild = await get_support_server(request.app.bot)
    try:
        await request.app.bot.rest.add_user_to_guild(
            access_token, guild.id, int(user_id)
        )
    except hikari.HikariError as e:
        print(e)
        return web.json_response(
            {"success": False, "error": "unable to add member to the server"}
        )

    return web.json_response({"success": True})


async def create_ticket(request: web.Request):
    body = await request.json()
    asyncio.get_event_loop().create_task(start_ticket(request.app.bot, body))
    return web.json_response({"success": True})


async def members(request):
    support_server = await get_support_server(request.app.bot)
    all_member = support_server.get_members().values()

    return web.json_response(
        {
            "members": list(
                filter(
                    None,
                    map(
                        lambda member: (
                            {
                                "name": member.display_name,
                                "username": member.username,
                                "id": str(member.id),
                                "avatar_url": member.avatar_url.url,
                            }
                            if not member.is_bot
                            else None
                        ),
                        all_member,
                    ),
                )
            )
        }
    )

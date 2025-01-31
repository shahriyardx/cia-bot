import asyncio

import hikari
from aiohttp import web

from src.utils import get_support_server
from src.utils.ticket import handle_ticket_start, approver_action, handle_ticket_init


async def index(req):
    return web.HTTPFound("https://coverticealliance.com")


async def add_to_server(bot: hikari.GatewayBot, request: web.Request):
    body = await request.json()

    access_token = body.get("access_token")
    user_id = body.get("user_id")

    print(f"{access_token} {user_id}")

    guild = await get_support_server(bot)
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


async def initialize_ticket(bot: hikari.GatewayBot, request: web.Request):
    await handle_ticket_init(bot, request)
    return web.json_response({"success": True})


async def start_ticket(bot: hikari.GatewayBot, request: web.Request):
    asyncio.get_event_loop().create_task(handle_ticket_start(bot, request))
    return web.json_response({"success": True})


async def members(bot: hikari.GatewayBot, request):
    support_server = await get_support_server(bot)
    all_members = support_server.get_members().values()
    non_bot_members = filter(lambda member: member.is_bot == False, all_members)

    return web.json_response(
        {
            "members": list(
                map(
                    lambda member: (
                        {
                            "name": member.display_name,
                            "username": member.username,
                            "id": str(member.id),
                            "avatar_url": (
                                member.avatar_url.url if member.avatar_url else ""
                            ),
                        }
                    ),
                    non_bot_members,
                ),
            )
        }
    )


async def is_approver(bot: hikari.GatewayBot, req: web.Request):
    user_id = int(req.match_info.get("user_id"))
    support_server = await get_support_server(bot)
    member = support_server.get_member(user_id)

    status = {
        "approver": False,
        "commissioner": False,
    }
    if not member:
        return web.json_response(status)

    if 1299126429094514729 in member.role_ids:
        status["approver"] = True

    if 1283055661889880225 in member.role_ids:
        status["commissioner"] = True

    return web.json_response(status)


async def finalize_ticket(bot: hikari.GatewayBot, req: web.Request):
    ticket_id = req.match_info.get("ticket_id")
    print("finalizing", ticket_id)
    await approver_action(bot, ticket_id)

    return web.json_response({"success": True})

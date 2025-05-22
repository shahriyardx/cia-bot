import hikari
from aiohttp import web

from src import database
from src.utils import get_support_server
from src.utils.ticket import approver_action, handle_ticket_init, handle_ticket_start
from prisma.enums import Position


async def sync_profile(bot: hikari.GatewayBot, request: web.Request):
    support_server = await get_support_server(bot)
    user_id = request.match_info["user_id"]  # userinfo id

    user_info = await database.userinfo.find_first(
        where={
            "id": user_id,
        }
    )

    settings = await database.settings.find_first()
    roles = await database.roles.find_first()

    reg = await database.seasonalregistration.find_first(
        where={"userInfoId": user_info.id, "seasonId": settings.seasonId}
    )

    member = support_server.get_member(int(user_info.discordId))
    if not member:
        return web.json_response(
            {"success": False, "error": "Unable to find your profile on discord server"}
        )

    nick = (
        user_info.psn
        if user_info.primaryConsole == "playstation"
        else user_info.gamertag
    )

    await member.edit(nickname=nick)

    position_roles = {
        Position.left_wing: roles.left_wing,
        Position.right_wing: roles.right_wing,
        Position.left_defense: roles.left_defense,
        Position.right_defense: roles.right_defense,
        Position.center: roles.center,
        Position.goalie: roles.goalie,
    }

    pp = position_roles.get(reg.primaryPosition if reg else user_info.primaryPosition)
    sp = position_roles.get(reg.secondaryPosition if reg else user_info.secondaryPosition)

    for val in position_roles.values():
        await member.remove_role(int(val))

    await member.add_role(int(pp))
    await member.add_role(int(sp))

    return web.json_response(
        {
            "success": True,
        }
    )

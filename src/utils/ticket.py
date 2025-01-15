import asyncio
import datetime
from typing import Sequence
from aiohttp import web

import hikari
from hikari import GatewayBot
from prisma.models import VotingTickets
from prisma.enums import VotingApproval


from src.utils.database import database, get_support_server
from src.utils.env import env
from .misc import find


async def get_ticket(server: hikari.GatewayGuild, user_id: int):
    def ticket_filter(channel: hikari.PermissibleGuildChannel):
        return (
            channel.parent_id == 1283055662468694027
            and channel.type == hikari.ChannelType.GUILD_TEXT
        )

    tickets: Sequence[hikari.TextableGuildChannel] = list(
        filter(ticket_filter, server.get_channels().values())
    )

    return find(
        tickets,
        lambda ticket: str(user_id) in ticket.name and "closed" not in ticket.name,
    )


async def handle_ticket_init(bot: hikari.GatewayBot, request: web.Request):
    server = await get_support_server(bot)
    ticket_id = request.match_info.get("ticket_id")
    ticket = await database.votingtickets.find_first(where={"id": ticket_id})

    user = await database.user.find_first(where={"id": ticket.userId})
    user_info = await database.userinfo.find_first(where={"userId": user.id})

    player = server.get_member(int(user_info.discordId))
    inviter = server.get_member(int(user_info.inviterId))

    await inviter.send(
        content=(
            f"{player.mention} stated that you have invited them to the league. "
            "Please click the link below to confirm or reject."
            "You must click the link within 24 hours from now. \n"
            f"<{env.LIVE_SITE}/ticket/{ticket_id}/inviter>"
        )
    )


async def handle_ticket_start(bot: hikari.GatewayBot, request: web.Request):
    server = await get_support_server(bot)
    ticket_id = request.match_info.get("ticket_id")
    ticket = await database.votingtickets.find_first(where={"id": ticket_id})

    user = await database.user.find_first(where={"id": ticket.userId})
    player = server.get_member(int(user.discordId))

    cia_role = server.get_role(1283055661403476057)  # CIA role id
    vote_channel: hikari.TextableGuildChannel = server.get_channel(1326635348100382852)

    if ticket.approved_by_inviter == "no":
        await player.send(
            content=(
                f"Hello {player.mention}, you did not pass the league vote to grant you access into the league. "
                "You have been banned from the league at this time and can appeal the vote in the following discord \n\n"
                "https://discord.gg/TEScsJAsH5 \n\n"
                "- CIA Commissioners"
            )
        )

        try:
            print("Banning user")
            await player.ban(reason="Did not pass leage vote to join league.")
        except Exception as e:
            print("Failed to ban user")
            print(e)

        return
    else:
        future = datetime.datetime.now() + datetime.timedelta(hours=24)
        ticket = await database.votingtickets.update(
            where={"id": ticket_id}, data={"expres": future}
        )

        await vote_channel.send(
            f"{cia_role.mention} Please vote on allowing {player.mention} access to the league. "
            f"\nClick this link to vote <{env.LIVE_SITE}/ticket/{ticket_id}/vote>\n"
            f"Voting Ends: <t:{int(ticket.expires.timestamp())}:f>",
            user_mentions=True,
            role_mentions=True,
        )

        await bot.scheduler.schedule_ticket(ticket)


async def handle_ticket_end(bot: GatewayBot, ticket: VotingTickets):
    await database.votingtickets.update(where={"id": ticket.id}, data={"expired": True})


async def approver_action(bot: GatewayBot, ticket_id: str):
    ticket = await database.votingtickets.find_first(where={"id": ticket_id})
    if not ticket:
        return

    server = await get_support_server(bot)
    user = await database.user.find_first(where={"id": ticket.userId})
    user_info = await database.userinfo.find_first(where={"userId": user.id})
    player = server.get_member(int(user_info.discordId))

    if ticket.approved == VotingApproval.yes:
        await player.add_role(1283055661403476057)
        await player.remove_role(1283055661403476056)
        return

    await player.send(
        content=(
            f"Hello {player.mention}, you did not pass the league vote to grant you access into the league. "
            "You have been banned from the league at this time and can appeal the vote in the following discord \n\n"
            "https://discord.gg/TEScsJAsH5 \n\n"
            "- CIA Commissioners"
        )
    )

    try:
        print("Banning user")
        await player.ban(reason="Did not pass leage vote to join league.")
    except Exception as e:
        print("Failed to ban user")
        print(e)

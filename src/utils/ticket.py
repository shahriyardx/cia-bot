import asyncio
import datetime
from typing import Sequence

import hikari
from hikari import GatewayBot
from prisma.models import VotingTickets

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


async def start_ticket(bot: hikari.GatewayBot, body):
    server = await get_support_server(bot)

    ticket_id = body.get("ticket_id")
    if not ticket_id:
        return

    ticket = await database.votingtickets.find_first(where={"id": ticket_id})
    if not ticket:
        return

    user = await database.user.find_first(where={"id": ticket.userId})
    user_info = await database.userinfo.find_first(where={"userId": user.id})

    player = server.get_member(int(user_info.discordId))
    inviter = server.get_member(int(user_info.inviterId))

    cia_role = server.get_role(1283055661403476057)  # CIA role id
    vote_channel = server.get_channel(1326635348100382852)

    await inviter.send(
        content=(
            f"{player.mention} stated that you have invited them to the league. "
            "Please click the link below to confirm or reject."
            "You must click the link within 24 hours from now. \n"
            f"<{env.LIVE_SITE}/ticket/{ticket_id}/inviter>"
        )
    )

    # await vote_channel.send(
    #     f"{cia_role.mention} Please vote on allowing {player.mention} access to the league. "
    #     f"\nClick this link to vote <{env.LIVE_SITE}/ticket/{ticket_id}/vote>\n"
    #     f"Voting Ends: <t:{int(ticket.expires.timestamp())}:f>"
    # )

    await bot.scheduler.schedule_ticket(ticket)


async def handle_ticket(bot: GatewayBot, ticket: VotingTickets):
    user = await database.user.find_first(where={"id": ticket.userId})
    votes = await database.vote.find_many(where={"votingTicketsId": ticket.id})

    server = await get_support_server(bot)
    player = server.get_member(int(user.discordId))
    ticket_channel = await get_ticket(server, user.discordId)

    print(user, server, player, ticket_channel)

    yes = 0
    no = 0

    for vote in votes:
        if vote.action == "up":
            yes += 1
        else:
            no += 1

    print("Votes", yes, no)

    if no > yes:
        try:
            await player.send(
                content=(
                    f"Hello {player.mention}, you did not pass the league vote to grant you access into the league. "
                    "You have been banned from the league at this time and can appeal the vote in the following discord \n\n"
                    "https://discord.gg/TEScsJAsH5 \n\n"
                    "- CIA Commissioners"
                )
            )
        except hikari.HikariError:
            pass

        try:
            print("Banning...")
            # await player.ban(
            #     reason=f"turned down by the league vote Yes: {yes}, No: {no}"
            # )
        except hikari.HikariError:
            print("Failed to ban")
            pass

        await ticket_channel.send(content=f"$close")
        await database.votingtickets.update(
            where={"id": ticket.id}, data={"expired": True}
        )
        return

    await database.votingtickets.update(where={"id": ticket.id}, data={"expired": True})
    cia_role = server.get_role(1283055661403476057)
    commissioner_role = server.get_role(1299126429094514729)

    await ticket_channel.send(content=f"$remove {cia_role.mention}")
    await ticket_channel.send(content=f"$add {commissioner_role.mention}")

    view = bot.rest.build_message_action_row()
    view.add_interactive_button(
        hikari.ButtonStyle.SUCCESS, "approve_player", label="Approve"
    )
    view.add_interactive_button(hikari.ButtonStyle.DANGER, "deny_player", label="Deny")

    await ticket_channel.send(
        content=f"{commissioner_role.mention} Do you approve the league vote of allowing {player.mention} into the league?",
        component=view,
    )

    await database.votingtickets.update(where={"id": ticket.id}, data={"expired": True})


async def handle_approval_interaction(
    bot: GatewayBot, interaction: hikari.ComponentInteraction
):

    await interaction.create_initial_response(
        hikari.ResponseType.DEFERRED_MESSAGE_CREATE,
        flags=hikari.MessageFlag.EPHEMERAL,
    )

    server = await get_support_server(bot)
    is_approver = find(
        server.get_member(interaction.user.id).get_roles(),
        lambda role: role.id == 1299126429094514729,
    )

    if not is_approver:
        return await interaction.edit_initial_response(
            content="You are not allowed to click this button",
        )

    server = await get_support_server(bot)
    ticket = await database.ticket.find_first(
        where={"message_id": str(interaction.message.id)}
    )
    player = server.get_member(int(ticket.user_id))
    ticket_channel = interaction.get_channel()

    approved = interaction.custom_id == "approve_player"

    view = bot.rest.build_message_action_row()
    view.add_interactive_button(hikari.ButtonStyle.SUCCESS, "appr_yes", label="Yes")
    view.add_interactive_button(hikari.ButtonStyle.DANGER, "appr_no", label="No")

    await interaction.edit_initial_response(
        content=(
            f"## Are you absolutely sure?\nYou are about to "
            f"{'deny' if interaction.custom_id == 'deny_player' else 'approve'} "
            f"{player.mention}'s access to the league"
        ),
        component=view,
    )

    def check(event: hikari.InteractionCreateEvent):
        if not isinstance(event.interaction, hikari.ComponentInteraction):
            return False

        return (
            event.interaction.user.id == interaction.user.id
            and interaction.channel_id == int(ticket.channel_id)
            and event.interaction.custom_id in ["appr_yes", "appr_no"]
        )

    event: hikari.InteractionCreateEvent = await bot.wait_for(
        hikari.InteractionCreateEvent, predicate=check, timeout=None
    )
    appr_interaction: hikari.ComponentInteraction = event.interaction
    confirmed = appr_interaction.custom_id == "appr_yes"

    await appr_interaction.create_initial_response(
        response_type=hikari.ResponseType.DEFERRED_MESSAGE_UPDATE
    )
    await appr_interaction.delete_initial_response()

    if approved and confirmed:
        await interaction.message.edit(
            component=None, content=f"{player.mention} has been approved"
        )

        cia_role = server.get_role(1283055661403476057)
        waiting_room_role = server.get_role(1283055661403476056)

        await player.remove_role(waiting_room_role)
        await player.add_role(cia_role)

        await ticket_channel.send(content=f"$close")

    elif not approved and confirmed:
        await interaction.message.edit(
            component=None, content=f"{player.mention} has been denied"
        )

        try:
            await player.send(
                content=(
                    f"Hello {player.mention}, you did not pass the league vote to grant you access into the league. "
                    "You have been banned from the league at this time and can appeal the vote in the following discord \n\n"
                    "https://discord.gg/TEScsJAsH5 \n\n"
                    "- CIA Commissioners"
                )
            )
        except hikari.HikariError:
            pass

        try:
            print("Banning...")
            # await player.ban(
            #     reason=f"turned down by the league vote Yes: {yes}, No: {no}"
            # )
        except hikari.HikariError:
            pass

        await ticket_channel.send("$close")
        return

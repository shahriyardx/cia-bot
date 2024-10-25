import asyncio
import datetime
from typing import Sequence

import hikari
from hikari import GatewayBot
from prisma.models import Ticket

from src.utils.database import database, get_support_server

from .misc import find


async def delete_ticket(ticket: Ticket):
    await database.ticket.delete(where={"id": ticket.id})


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
    user_id = body.get("user_id")
    if not user_id:
        return

    user_info = await database.userinfo.find_first(where={"id": user_id})
    if not user_info:
        return

    server = await get_support_server(bot)
    bot_util_channel: hikari.TextableGuildChannel = server.get_channel(
        1283055665514024968
    )

    ticket = await get_ticket(server, user_info.discordId)

    if not ticket:
        await bot_util_channel.send(f"$new {user_info.discordId}")
        await asyncio.sleep(5)

    ticket = await get_ticket(server, user_info.discordId)

    player = server.get_member(int(user_info.discordId))
    inviter = server.get_member(int(user_info.inviterId))

    view = bot.rest.build_message_action_row()
    view.add_interactive_button(hikari.ButtonStyle.SUCCESS, "yes", label="Yes")
    view.add_interactive_button(hikari.ButtonStyle.DANGER, "no", label="No")

    await ticket.send(content=f"$add ${inviter.id}")
    await ticket.send(
        content=f"{inviter.mention} did you invite {player.mention}",
        component=view,
    )

    def check(event: hikari.InteractionCreateEvent):
        if not isinstance(event.interaction, hikari.ComponentInteraction):
            return False

        interaction = event.interaction
        if interaction.user.id != inviter.id:
            return False

        return True

    event: hikari.InteractionCreateEvent = await bot.wait_for(
        hikari.InteractionCreateEvent, predicate=check, timeout=None
    )
    interaction: hikari.ComponentInteraction = event.interaction

    await interaction.create_initial_response(
        component=None, response_type=hikari.ResponseType.MESSAGE_UPDATE
    )

    if interaction.custom_id == "no":
        await ticket.send("$close")
        return

    cia_role = server.get_role(1283055661403476057)  # CIA role id
    await ticket.send(f"$add {cia_role.mention}")

    vote_message = await ticket.send(
        f"{cia_role.mention} Please vote on allowing {player.mention} access to the league."
    )

    yes_emoji = find(server.get_emojis().values(), lambda emoji: emoji.name == "yes")
    no_emoji = find(server.get_emojis().values(), lambda emoji: emoji.name == "no")

    await vote_message.add_reaction(yes_emoji)
    await vote_message.add_reaction(no_emoji)

    task_time = datetime.datetime.now(tz=None) + datetime.timedelta(hours=24)

    task = await database.ticket.create(
        {
            "time": task_time,
            "channel_id": str(ticket.id),
            "message_id": str(vote_message.id),
            "user_id": str(player.id),
            "step": 1,
        }
    )

    await bot.scheduler.schedule_ticket(task)


async def get_ticket_info(bot: GatewayBot, ticket: Ticket):
    server = await get_support_server(bot)
    player = server.get_member(int(ticket.user_id))

    ticket_channel: hikari.GuildTextChannel = server.get_channel(int(ticket.channel_id))

    if not ticket_channel:
        await delete_ticket(ticket)
        raise ValueError("")

    try:
        message = await bot.rest.fetch_message(
            ticket_channel.id, int(ticket.message_id)
        )
    except hikari.HikariError:
        await delete_ticket(ticket)
        raise ValueError("")

    reactions = message.reactions

    yes = 0
    no = 0

    for react in reactions:
        if react.emoji.name == "yes":
            yes = react.count

        if react.emoji.name == "no":
            no = react.count

    return [yes, no, server, player, ticket_channel]


async def handle_ticket(bot: GatewayBot, ticket: Ticket):
    yes, no, server, player, ticket_channel = await get_ticket_info(bot, ticket)

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
            await player.ban(
                reason=f"turned down by the league vote Yes: {yes}, No: {no}"
            )
        except hikari.HikariError:
            print("Failed to ban")
            pass

        await delete_ticket(ticket)
        await ticket_channel.send(content=f"$close")
        return

    cia_role = server.get_role(1283055661403476057)
    commissioner_role = server.get_role(1283055661889880225)

    await ticket_channel.send(content=f"$remove {cia_role.mention}")
    await ticket_channel.send(content=f"$add {commissioner_role.mention}")

    view = bot.rest.build_message_action_row()
    view.add_interactive_button(
        hikari.ButtonStyle.SUCCESS, "approve_player", label="Approve"
    )
    view.add_interactive_button(hikari.ButtonStyle.DANGER, "deny_player", label="Deny")

    approve_message = await ticket_channel.send(
        content=f"{commissioner_role.mention} Do you approve the league vote of allowing {player.mention} into the league?",
        component=view,
    )

    task_time = datetime.datetime.now(tz=None) + datetime.timedelta(hours=24)

    await database.ticket.update(
        where={"id": ticket.id},
        data={"message_id": str(approve_message.id), "step": 2, "time": task_time},
    )


async def handle_approval_interaction(
    bot: GatewayBot, interaction: hikari.ComponentInteraction
):
    server = await get_support_server(bot)
    ticket = await database.ticket.find_first(
        where={"message_id": str(interaction.message.id)}
    )
    player = server.get_member(int(ticket.user_id))
    ticket_channel = interaction.get_channel()

    is_approver = find(
        server.get_member(interaction.user.id).get_roles(),
        lambda role: role.id == 1299126429094514729,
    )

    if not is_approver:
        return await interaction.create_initial_response(
            hikari.ResponseType.MESSAGE_CREATE,
            flags=hikari.MessageFlag.EPHEMERAL,
            content="You are not allowed to click this button",
        )

    approved = interaction.custom_id == "approve_player"

    await interaction.create_initial_response(
        hikari.ResponseType.DEFERRED_MESSAGE_CREATE, flags=hikari.MessageFlag.EPHEMERAL
    )

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

        await delete_ticket(ticket)
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

        await delete_ticket(ticket)
        await ticket_channel.send("$close")
        return

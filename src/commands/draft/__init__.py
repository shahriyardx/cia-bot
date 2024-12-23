from typing import List

import hikari
import miru

from src.types import CiaBot
from src.utils.database import database, get_support_server

from ..utils import Command, defer
from ..utils.flags import DEFERRED_CREATE, LOADING, LOADING_EPHEMERAL, NONE
from .view import DraftView


@defer(LOADING, DEFERRED_CREATE)
async def draft(bot: CiaBot, interaction: hikari.CommandInteraction):
    client = miru.Client(bot)
    settings = await database.settings.find_first()

    clubs = await database.club.find_many()
    club_options = list(
        map(
            lambda club: hikari.SelectMenuOption(
                label=club.name,
                value=club.id,
                description=None,
                is_default=False,
                emoji=None,
            ),
            clubs,
        )
    )

    view = DraftView(
        clubs=club_options,
    )(timeout=None)

    await interaction.edit_initial_response(
        content="Select member and team", components=view.build()
    )

    client.start_view(view, bind_to=interaction)
    await view.wait()

    if view.cancelled:
        return await interaction.edit_initial_response(
            content="Cancelled draft", components=None
        )

    await interaction.edit_initial_response(
        content="Checking draft ability", components=[]
    )

    member_ids: List[str] = list(map(lambda member: str(member.id), view.members))
    club_id: str = view.club_id[0]
    print(member_ids, club_id)

    if not club_id or not member_ids:
        return await interaction.edit_initial_response(
            content="Please select both members and team to proceed", components=[]
        )

    datas = []

    for member_id in member_ids:
        member = interaction.get_guild().get_member(int(member_id))
        signed_up = await database.userinfo.find_first(
            where={"discordId": member_id}, include={"user": True}
        )
        if not signed_up:
            return await interaction.edit_initial_response(
                content=f"{member.mention} is not signed up"
            )

        registered = await database.seasonalregistration.find_first(
            where={"userInfoId": signed_up.id, "seasonId": settings.seasonId}
        )

        if not registered:
            return await interaction.edit_initial_response(
                content=f"{member.mention} is not registered for this season"
            )

        drafted = await database.seasonaldraft.find_first(
            where={"userInfoId": signed_up.id, "seasonId": settings.seasonId},
            include={"club": True},
        )

        if drafted:
            return await interaction.edit_initial_response(
                content=f"{member.mention} is already drafted for team `{drafted.club.name}`"
            )

        datas.append(
            {
                "clubId": club_id,
                "seasonId": settings.seasonId,
                "userInfoId": signed_up.id,
                "userId": signed_up.user.id,
            }
        )

    for data in datas:
        await database.seasonaldraft.create(data=data)

    await interaction.edit_initial_response(
        content="All the members has been drafted", components=[]
    )


commands: List[Command] = [
    Command(
        name="draft",
        description="Draft player for a team",
        callback=draft,
        permissions=hikari.Permissions.NONE,
        options=[],
        guild_ids=[],
    )
]

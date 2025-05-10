from typing import List

import hikari
import miru

from src.types import CiaBot
from src.utils.database import database, get_support_server

from ..utils import Command, defer
from ..utils.flags import DEFERRED_CREATE, LOADING, LOADING_EPHEMERAL, NONE
from .utils import get_option_values
from .view import DraftView


@defer(LOADING, DEFERRED_CREATE)
async def draft(_bot: CiaBot, interaction: hikari.CommandInteraction):
    settings = await database.settings.find_first()
    options = get_option_values(interaction)

    member: hikari.InteractionMember = options["member"]
    team: hikari.Role = options["team"]
    rd: int = options["round"]

    club = await database.club.find_first(where={"name": team.name})

    if not club:
        return await interaction.edit_initial_response(
            content=f"{team} is not not a valid team"
        )

    signed_up = await database.userinfo.find_first(
        where={"discordId": str(member.id)}, include={"user": True}
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

    await database.seasonaldraft.create(
        {
            "clubId": club.id,
            "seasonId": settings.seasonId,
            "userInfoId": signed_up.id,
            "userId": signed_up.user.id,
            "role": "player",
            "round": int(rd),
        }
    )

    await interaction.edit_initial_response(
        content=f"{member.mention} has been drafted for team {team.mention}",
        components=[],
    )

    await member.add_role(team)


@defer(LOADING, DEFERRED_CREATE)
async def assign(bot: CiaBot, interaction: hikari.CommandInteraction):
    settings = await database.settings.find_first()
    options = get_option_values(interaction)

    member: hikari.InteractionMember = options["member"]
    team: hikari.Role = options["team"]
    position = options["position"]

    club = await database.club.find_first(where={"name": team.name})
    signed_up = await database.userinfo.find_first(
        where={"discordId": str(member.id)}, include={"user": True}
    )
    drafted = await database.seasonaldraft.find_first(
        where={"userInfoId": signed_up.id, "seasonId": settings.seasonId},
        include={"club": True},
    )

    if not club:
        return await interaction.edit_initial_response(
            content=f"{team} is not not a valid team"
        )

    if drafted:
        return await interaction.edit_initial_response(
            content=f"{member.mention} is already drafted for team `{drafted.club.name}`"
        )

    await database.seasonaldraft.create(
        {
            "clubId": club.id,
            "seasonId": settings.seasonId,
            "userInfoId": signed_up.id,
            "userId": signed_up.user.id,
            "role": position,
        }
    )

    await interaction.edit_initial_response(
        content=f"{member.mention} has been assigned {position} for {team}",
        components=None,
    )


commands: List[Command] = [
    Command(
        name="draft",
        description="Draft player for a team",
        callback=draft,
        permissions=hikari.Permissions.NONE,
        options=[
            hikari.CommandOption(
                type=hikari.OptionType.ROLE,
                name="team",
                description="The Team",
                is_required=True,
            ),
            hikari.CommandOption(
                type=hikari.OptionType.USER,
                name="member",
                description="The member",
                is_required=True,
            ),
            hikari.CommandOption(
                type=hikari.OptionType.INTEGER,
                name="round",
                description="The round",
                is_required=True,
                choices=[
                    hikari.CommandChoice(name="1st", value=1),
                    hikari.CommandChoice(name="2nd", value=2),
                    hikari.CommandChoice(name="3rd", value=3),
                    hikari.CommandChoice(name="4th", value=4),
                    hikari.CommandChoice(name="5th", value=5),
                    hikari.CommandChoice(name="6th", value=6),
                    hikari.CommandChoice(name="7th", value=7),
                    hikari.CommandChoice(name="8th", value=8),
                    hikari.CommandChoice(name="9th", value=9),
                    hikari.CommandChoice(name="10th", value=10),
                    hikari.CommandChoice(name="11th", value=11),
                    hikari.CommandChoice(name="12th", value=12),
                    hikari.CommandChoice(name="13th", value=13),
                ],
            ),
        ],
        guild_ids=[1283055660866600960],
    ),
    Command(
        name="assign",
        description="Assign owner and gm player for a team",
        callback=assign,
        permissions=hikari.Permissions.NONE,
        options=[
            hikari.CommandOption(
                type=hikari.OptionType.ROLE,
                name="team",
                description="The Team",
                is_required=True,
            ),
            hikari.CommandOption(
                type=hikari.OptionType.USER,
                name="member",
                description="The member",
                is_required=True,
            ),
            hikari.CommandOption(
                type=hikari.OptionType.STRING,
                name="position",
                description="select the position",
                is_required=True,
                choices=[
                    hikari.CommandChoice(name="Owner", value="owner"),
                    hikari.CommandChoice(name="GM", value="gm"),
                ],
            ),
        ],
        guild_ids=[1283055660866600960],
    ),
]

from typing import List

import hikari

from src.utils.database import database

from .utils import Command, defer
from .utils.flags import DEFERRED_CREATE, LOADING, LOADING_EPHEMERAL, NONE
from .utils.misc import generate_random_string


@defer(LOADING, DEFERRED_CREATE)
async def help_command(_bot, interaction: hikari.CommandInteraction):
    await interaction.edit_initial_response(content="This will be the help message")


@defer(LOADING_EPHEMERAL, DEFERRED_CREATE)
async def generate_invite_code(_bot, interaction: hikari.CommandInteraction):
    existing_code = await database.invitecode.find_first(
        where={"userId": str(interaction.user.id)}
    )
    if existing_code:
        await interaction.edit_initial_response(
            content=f"Your invite code is {existing_code.code}"
        )

    code = generate_random_string(5)
    await database.invitecode.create(
        data={
            "userId": str(interaction.user.id),
            "code": code,
        }
    )


commands: List[Command] = [
    Command(
        name="help",
        description="See bot's help",
        callback=help_command,
        permissions=NONE,
        options=[],
        guild_ids=[],
    )
]

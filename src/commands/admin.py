import asyncio
from typing import List, Sequence

import hikari

from src.types import CiaBot
from src.utils.database import get_support_server

from .utils import Command, defer
from .utils.flags import DEFERRED_CREATE, LOADING_EPHEMERAL, NONE


@defer(LOADING_EPHEMERAL, DEFERRED_CREATE)
async def sync_commands(bot: CiaBot, interaction: hikari.CommandInteraction):
    await bot.register_commands()
    await interaction.edit_initial_response(content="Sync finished")


commands: List[Command] = [
    Command(
        name="sync-commands",
        description="Sync all commands",
        callback=sync_commands,
        permissions=hikari.Permissions.ADMINISTRATOR,
        options=[],
        guild_ids=[],
    ),
]

from dataclasses import dataclass, field
from typing import Callable, List

import hikari

# Response types
DEFERRED_CREATE = hikari.ResponseType.DEFERRED_MESSAGE_CREATE
DEFERRED_UPDATE = hikari.ResponseType.DEFERRED_MESSAGE_UPDATE

# Message flags
LOADING = hikari.MessageFlag.LOADING
EPHEMERAL = hikari.MessageFlag.EPHEMERAL
LOADING_EPHEMERAL = LOADING | EPHEMERAL

# Permissions
NONE = hikari.Permissions.NONE
ADMIN = hikari.Permissions.ADMINISTRATOR


@dataclass
class Command:
    name: str
    description: str
    callback: Callable
    permissions: hikari.Permissions
    options: List[hikari.CommandOption]
    guild_ids: List[int] = field(default_factory=lambda: [])


def defer(flags, response_type):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            interaction: hikari.CommandInteraction = (
                kwargs.get("interaction") or args[1]
            )
            await interaction.create_initial_response(
                flags=flags, response_type=response_type
            )
            await func(*args, **kwargs)

        return wrapper

    return decorator

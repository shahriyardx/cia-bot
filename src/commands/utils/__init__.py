from dataclasses import dataclass, field
from typing import Callable, List

import hikari


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

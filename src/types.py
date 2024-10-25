from dataclasses import dataclass

from hikari import GatewayBot

from src.utils.scheduler import Scheduler


@dataclass
class CiaBot(GatewayBot):
    scheduler: Scheduler

    async def register_commands(self) -> None: ...

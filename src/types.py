from dataclasses import dataclass

from hikari import GatewayBot
from miru import Client

from src.utils.scheduler import Scheduler


@dataclass
class CiaBot(GatewayBot):
    scheduler: Scheduler
    miru: Client

    async def register_commands(self) -> None: ...

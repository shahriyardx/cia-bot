import asyncio
from datetime import datetime, timedelta
from typing import Awaitable

import hikari
from prisma.models import VotingTickets

from .ticket import handle_ticket


def get_delta(execution_time: datetime) -> float:
    now = datetime.now().replace(tzinfo=None)
    execution_time = execution_time.replace(tzinfo=None)

    if execution_time <= now:
        return 0

    return (execution_time - now).total_seconds()


class Scheduler:
    def __init__(self, bot: hikari.GatewayBot):
        self.bot = bot

    async def start_ticket_task(self, ticket: VotingTickets) -> None:
        seconds = get_delta(ticket.expires)

        if seconds > 0:
            await asyncio.sleep(seconds)
            await handle_ticket(self.bot, ticket)
            return

        await handle_ticket(self.bot, ticket)

    @staticmethod
    async def start_coro_task(time: datetime, coro: Awaitable) -> None:
        seconds = get_delta(time)

        if seconds > 0:
            await asyncio.sleep(seconds)
            await coro
            return

        await coro

    async def schedule_ticket(self, ticket: VotingTickets) -> asyncio.Task:
        return asyncio.get_event_loop().create_task(self.start_ticket_task(ticket))

    async def schedule_coro(self, time: datetime, coro: Awaitable) -> asyncio.Task:
        return asyncio.get_event_loop().create_task(self.start_coro_task(time, coro))

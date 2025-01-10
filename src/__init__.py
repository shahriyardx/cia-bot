from typing import Dict

import hikari
import miru
from datetime import datetime
from src.commands import draft_commands, admin_commands, user_commands
from src.commands.utils import Command
from src.utils import database, env
from src.utils.scheduler import Scheduler

from .api import start_api


class CiaBot(hikari.GatewayBot):
    def __init__(self, token: str, **kwargs):
        super().__init__(token, intents=hikari.Intents.ALL, logs="ERROR", **kwargs)

        self.scheduler = Scheduler(self)
        self.global_commands: Dict[str, Command] = {}
        self.miru = miru.Client(self)
        self.subscribe(hikari.StartedEvent, self.on_ready)
        self.subscribe(hikari.InteractionCreateEvent, self.handle_interaction)

    def build_command(self, command: Command):
        self.global_commands[command.name] = command

        cmd = self.rest.slash_command_builder(
            name=command.name, description=command.description
        )

        for option in command.options:
            cmd.add_option(option)

        cmd.set_default_member_permissions(command.permissions)
        return cmd

    async def cache_commands(self):
        for command in [*admin_commands, *user_commands, *draft_commands]:
            self.global_commands[command.name] = command

    async def register_commands(self):
        app = await self.rest.fetch_application()
        cmds = map(self.build_command, user_commands)
        await self.rest.set_application_commands(app, list(cmds))

        # only support server commands
        settings = await database.settings.find_first()
        if not settings:
            return

        support_server_id = int(settings.support_server)
        cmds = map(self.build_command, [*admin_commands, *draft_commands])
        await self.rest.set_application_commands(
            app, list(cmds), guild=support_server_id
        )

    async def schedule_tickets(self):
        tickets = await database.votingtickets.find_many(where={"expired": False})

        for ticket in tickets:
            await self.scheduler.schedule_ticket(ticket)

    async def on_ready(self, _):
        await database.connect()
        await self.cache_commands()
        await self.schedule_tickets()
        await start_api(self)

        print(f"❤️ Bot is ready", self.get_me())

    async def handle_interaction(self, event: hikari.InteractionCreateEvent):
        interaction = event.interaction
        if isinstance(interaction, hikari.CommandInteraction):
            command = self.global_commands.get(interaction.command_name)
            if command:
                await command.callback(self, interaction)


bot = CiaBot(token=env.TOKEN)

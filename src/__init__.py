from typing import Dict

import hikari

from src.commands import commands
from src.commands.utils import Command
from src.utils import database, env
from src.utils.scheduler import Scheduler
from src.utils.ticket import handle_approval_interaction

from .api import start_api


class CiaBot(hikari.GatewayBot):
    def __init__(self, token: str, **kwargs):
        super().__init__(token, intents=hikari.Intents.ALL, logs="ERROR", **kwargs)

        self.scheduler = Scheduler(self)
        self.global_commands: Dict[str, Command] = {}
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
        for command in commands:
            self.global_commands[command.name] = command

    async def register_commands(self):
        app = await self.rest.fetch_application()
        cmds = map(self.build_command, commands)
        await self.rest.set_application_commands(app, list(cmds))

    async def schedule_tickets(self):
        tickets = await database.ticket.find_many()

        for ticket in tickets:
            if ticket.step != 1:
                continue

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

        if isinstance(interaction, hikari.ComponentInteraction):
            if interaction.custom_id in ["approve_player", "deny_player"]:
                await handle_approval_interaction(self, interaction)


bot = CiaBot(token=env.TOKEN)

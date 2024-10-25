import aiohttp_cors
from aiohttp import web
from hikari import GatewayBot

from src.utils import env

from .middlewares import trailing_slash_middleware
from .routes import add_to_server, create_ticket, index, members


class Application(web.Application):
    def __init__(self, bot: GatewayBot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot


async def start_api(bot: GatewayBot):
    app = Application(bot, middlewares=[trailing_slash_middleware])

    app.router.add_get("/", index)
    app.router.add_get("/members/", members)
    app.router.add_put("/add-to-server/", add_to_server)
    app.router.add_post("/create-ticket/", create_ticket)

    cors = aiohttp_cors.setup(
        app,
        defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*",
            )
        },
    )

    for route in list(app.router.routes()):
        cors.add(route)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, env.API_HOST, env.API_PORT)
    await site.start()

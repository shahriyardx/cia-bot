import aiohttp_cors
from aiohttp import web
from hikari import GatewayBot

from src.utils import env

from .middlewares import trailing_slash_middleware
from .routes import (
    add_to_server,
    start_ticket,
    index,
    members,
    is_approver,
    finalize_ticket,
    initialize_ticket
)


class Application(web.Application):
    def __init__(self, bot: GatewayBot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot


async def start_api(bot: GatewayBot):
    app = Application(bot, middlewares=[trailing_slash_middleware])

    def bot_route(callback):
        async def wrapper(req: web.Request):
            return await callback(bot, req)

        return wrapper

    app.router.add_get("/", bot_route(index))
    app.router.add_get("/members/", bot_route(members))
    app.router.add_put("/add-to-server/", bot_route(add_to_server))
    app.router.add_get("/permissions/{user_id}/", bot_route(is_approver))
    app.router.add_post("/ticket/{ticket_id}/init/", bot_route(initialize_ticket))
    app.router.add_post("/ticket/{ticket_id}/start/", bot_route(start_ticket))
    app.router.add_post("/ticket/{ticket_id}/finalize/", bot_route(finalize_ticket))

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

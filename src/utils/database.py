import hikari
from prisma.models import Settings

from prisma import Prisma

database = Prisma()


async def get_settings() -> Settings:
    return await database.settings.find_first()


async def get_support_server(bot: hikari.GatewayBot) -> hikari.GatewayGuild:
    settings = await get_settings()
    return bot.cache.get_guild(int(settings.support_server))

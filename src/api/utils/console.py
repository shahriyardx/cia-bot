from src.utils.database import database


async def get_xapi_token():
    settings = await database.settings.find_first()
    return settings.xapi


async def get_npsso():
    settings = await database.settings.find_first()
    return settings.npsso

import asyncio

import hikari

from src import bot


async def start():
    await bot.start(
        afk=True,
        activity=hikari.Activity(
            name="Covert Ice Alliance", state="Creating the best league"
        ),
    )


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start())
    loop.run_forever()


if __name__ == "__main__":
    main()

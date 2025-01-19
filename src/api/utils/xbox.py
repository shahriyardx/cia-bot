import aiohttp

BASE_API = "https://xapi.us/api"


async def get_profile(token: str, gamertag: str):
    async with aiohttp.ClientSession() as session:
        session.headers["Authorization"] = f"Bearer {token}"
        async with session.get(f"{BASE_API}/{gamertag}/profile-for-gamertag") as resp:
            if resp.status == 200:
                data = await resp.json()
                data = {"account_id": data["id"], "username": gamertag}

                return {"success": True, "data": data}
            if resp.status == 429:
                return {
                    "success": False,
                    "error": "Too many requests, Please wait 1 minute",
                }
            if resp.status == 404:
                return {
                    "success": False,
                    "error": f"We are unable to find your xbox account with gamertag '{gamertag}'",
                }

    return {"success": False, "error": "Something went wrong"}


async def send_message(token: str, gamertag: str, message: str):
    data = await get_profile(token, gamertag)
    if data["success"] is False:
        return data

    account_id = data["data"]["account_id"]

    async with aiohttp.ClientSession() as session:
        session.headers["Authorization"] = f"Bearer {token}"
        async with session.post(
            f"{BASE_API}/messages",
            json={"to": [account_id], "message": message},
        ) as resp:
            if resp.status == 200:
                return {"success": True, "data": "message sent"}

            if resp.status == 429:
                return {
                    "success": False,
                    "error": "Too many requests, Please wait 1 minute",
                }

            if resp.status == 404:
                return {
                    "success": False,
                    "error": f"We are unable to find your xbox account with gamertag '{gamertag}'",
                }

    return {"success": False, "error": "Something went wrong"}


async def send_friend_request(token: str, gamertag: str):
    data = await get_profile(token, gamertag)
    if data["success"] is False:
        return data

    account_id = data["data"]["account_id"]
    async with aiohttp.ClientSession() as session:
        session.headers["Authorization"] = f"Bearer {token}"
        async with session.put(f"{BASE_API}/{account_id}/add-as-friend") as resp:
            if resp.status >= 200 and resp.status < 300:
                return {"success": True, "data": "request sent"}

            if resp.status == 429:
                return {
                    "success": False,
                    "error": "Too many requests, Please wait 1 minute",
                }

            if resp.status == 404:
                return {
                    "success": False,
                    "error": f"We are unable to find xbox account with gamertag '{gamertag}'",
                }

    return {"success": False, "error": "Something went wrong"}

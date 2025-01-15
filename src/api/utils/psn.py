from psnawp_api import PSNAWP
import traceback


def get_profile(token: str, online_id: str):
    api = PSNAWP(token)
    print("TOKEN", token)

    try:
        profile = api.user(online_id=online_id)
        data = {
            "account_id": profile.account_id,
            "username": profile.online_id,
        }

        return {"success": True, "data": data}
    except Exception:  # noqa
        traceback.print_exc()

        return {
            "success": False,
            "error": f"We are unable to find your playstation account with PSN '{online_id}'",
            "data": None,
        }


def send_message(token: str, online_id: str, message: str):
    api = PSNAWP(token)

    try:
        profile = api.user(online_id=online_id)
    except:
        return {
            "success": False,
            "error": f"We are unable to find your playstation account with PSN '{online_id}'",
        }

    try:
        new_group = api.group(users_list=[profile])
        new_group.send_message(message)

        return {
            "success": True,
        }

    except:
        return {"success": False, "error": "Unable to send message"}

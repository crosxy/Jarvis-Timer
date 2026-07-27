import requests
import urllib3

urllib3.disable_warnings()

URL = "https://127.0.0.1:2999/liveclientdata/allgamedata"


def get_data():
    try:
        r = requests.get(URL, verify=False, timeout=1)

        if r.status_code == 200:
            return r.json()

    except:
        return None

    return None
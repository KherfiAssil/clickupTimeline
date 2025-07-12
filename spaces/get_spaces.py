# clickup_api/lists/get_lists.py

from auth.oauth_handler import get_access_token
import requests

def get_spaces():
    token = get_access_token()
    headers = {"Authorization": token}
    url = "https://api.clickup.com/api/v2/space"
    response = requests.get(url, headers=headers)
    return response.json()

if __name__ == "__main__":
    data = get_spaces()
    for space in data.get("lists", []):
        print(f"📂 List: {space['name']} (ID: {space['id']})")

import sys
import os
import requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from auth.oauth_handler import get_access_token

def get_teams():
    token = get_access_token()
    headers = {"Authorization": token}
    url = "https://api.clickup.com/api/v2/team"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Erreur API ({response.status_code}) : {response.text}")
        return []
    return response.json().get("teams", [])

if __name__ == "__main__":
    teams = get_teams()
    if not teams:
        print("🚫 Aucune équipe trouvée.")
    else:
        print(f"📦 {len(teams)} équipe(s) trouvée(s) :\n")
        for team in teams:
            print(f"📂 Team : {team['name']} (ID: {team['id']})")

import sys
import os
import requests

# 🔁 Ajouter le dossier parent pour importer auth
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from auth.oauth_handler import get_access_token

def get_all_lists():
    token = get_access_token()
    headers = {"Authorization": token}

    # 🧱 1. Récupérer les teams (workspaces)
    teams_url = "https://api.clickup.com/api/v2/team"
    teams_response = requests.get(teams_url, headers=headers)
    if teams_response.status_code != 200:
        print(f"❌ Erreur team : {teams_response.text}")
        return []

    lists_data = []

    for team in teams_response.json().get("teams", []):
        team_id = team["id"]
        team_name = team["name"]

        # 📦 2. Récupérer les spaces
        spaces_url = f"https://api.clickup.com/api/v2/team/{team_id}/space"
        spaces_response = requests.get(spaces_url, headers=headers)
        for space in spaces_response.json().get("spaces", []):
            space_id = space["id"]
            space_name = space["name"]

            # 📁 3. Récupérer les folders
            folders_url = f"https://api.clickup.com/api/v2/space/{space_id}/folder"
            folders_response = requests.get(folders_url, headers=headers)
            for folder in folders_response.json().get("folders", []):
                folder_id = folder["id"]
                folder_name = folder["name"]

                # 📋 4. Récupérer les lists
                lists_url = f"https://api.clickup.com/api/v2/folder/{folder_id}/list"
                lists_response = requests.get(lists_url, headers=headers)
                for lst in lists_response.json().get("lists", []):
                    lists_data.append({
                        "team": team_name,
                        "space": space_name,
                        "folder": folder_name,
                        "list_id": lst["id"],
                        "list_name": lst["name"]
                    })

    return lists_data


if __name__ == "__main__":
    all_lists = get_all_lists()
    if not all_lists:
        print("🚫 Aucune liste trouvée.")
    else:
        print(f"📄 {len(all_lists)} listes trouvées :\n")
        for lst in all_lists:
            print(f"📂 {lst['list_name']} (ID: {lst['list_id']}) - Folder: {lst['folder']} - Space: {lst['space']} - Team: {lst['team']}")

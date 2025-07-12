import sys
import os
import requests

# 👉 Import du module d’auth
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from auth.oauth_handler import get_access_token


def get_all_tasks():
    token = get_access_token()
    headers = {"Authorization": token}
    all_tasks = []

    # 1. Récupérer les teams
    res_team = requests.get("https://api.clickup.com/api/v2/team", headers=headers)
    for team in res_team.json().get("teams", []):
        team_id = team["id"]
        team_name = team["name"]

        # 2. Récupérer les spaces
        res_spaces = requests.get(f"https://api.clickup.com/api/v2/team/{team_id}/space", headers=headers)
        for space in res_spaces.json().get("spaces", []):
            space_id = space["id"]
            space_name = space["name"]

            # 3. Récupérer les folders
            res_folders = requests.get(f"https://api.clickup.com/api/v2/space/{space_id}/folder", headers=headers)
            for folder in res_folders.json().get("folders", []):
                folder_id = folder["id"]
                folder_name = folder["name"]

                # 4. Récupérer les lists
                res_lists = requests.get(f"https://api.clickup.com/api/v2/folder/{folder_id}/list", headers=headers)
                for lst in res_lists.json().get("lists", []):
                    list_id = lst["id"]
                    list_name = lst["name"]

                    # 5. Récupérer les tasks
                    res_tasks = requests.get(f"https://api.clickup.com/api/v2/list/{list_id}/task", headers=headers)
                    for task in res_tasks.json().get("tasks", []):
                        all_tasks.append({
                            "task_id": task["id"],
                            "task_name": task["name"],
                            "status": task["status"]["status"],
                            "assignee": task["assignees"][0]["username"] if task["assignees"] else "Non assignée",
                            "created": task["date_created"],
                            "list_name": list_name,
                            "folder": folder_name,
                            "space": space_name,
                            "team": team_name
                        })
    return all_tasks


if __name__ == "__main__":
    tasks = get_all_tasks()
    print(f"\n✅ Total : {len(tasks)} tâches récupérées\n")
    for task in tasks:
        print(f"📌 {task['task_name']} ({task['status']}) - List: {task['list_name']} - Assignée à: {task['assignee']}")

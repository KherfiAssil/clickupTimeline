import sys
import os
import requests
import pandas as pd
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from auth.oauth_handler import get_access_token

def get_all_tasks_with_subtasks():
    token = get_access_token()
    headers = {"Authorization": token}
    all_tasks = []

    res_team = requests.get("https://api.clickup.com/api/v2/team", headers=headers)
    for team in res_team.json().get("teams", []):
        team_id = team["id"]
        team_name = team["name"]

        res_spaces = requests.get(f"https://api.clickup.com/api/v2/team/{team_id}/space", headers=headers)
        for space in res_spaces.json().get("spaces", []):
            space_id = space["id"]
            space_name = space["name"]

            res_folders = requests.get(f"https://api.clickup.com/api/v2/space/{space_id}/folder", headers=headers)
            for folder in res_folders.json().get("folders", []):
                folder_id = folder["id"]
                folder_name = folder["name"]

                res_lists = requests.get(f"https://api.clickup.com/api/v2/folder/{folder_id}/list", headers=headers)
                for lst in res_lists.json().get("lists", []):
                    list_id = lst["id"]
                    list_name = lst["name"]

                    url = f"https://api.clickup.com/api/v2/list/{list_id}/task?subtasks=true&include_closed=true"
                    res_tasks = requests.get(url, headers=headers)

                    for task in res_tasks.json().get("tasks", []):
                        task_type = "subtask" if task.get("parent") else "task"
                        created_date = int(task["date_created"]) / 1000 if task.get("date_created") else None
                        start_date = int(task["start_date"]) / 1000 if task.get("start_date") else None
                        due_date = int(task["due_date"]) / 1000 if task.get("due_date") else None

                        task_id = task["id"]
                        parent_id = task["parent"] if task_type == "subtask" and "parent" in task else task_id

                        priority_label = task["priority"]["priority"] if task.get("priority") and isinstance(task["priority"], dict) else "Non précisée"

                        if task.get("assignees"):
                            assignees = ", ".join([
                                a["username"] if a.get("username") else a.get("email", "Inconnu")
                                for a in task.get("assignees", [])
                            ])
                            if not assignees:
                                assignees = "Non assignée"

                        else:
                            assignees = "Non assignée"

                        assignees = ", ".join([
                            (a.get("username") or a.get("email", "Inconnu")).split("@")[0]
                            for a in task.get("assignees", [])
                        ]) or "Non assignée"


                        all_tasks.append({
                            "type": task_type,
                            "task_id": task_id,
                            "parent_id": parent_id,
                            "task_name": task["name"],
                            "status": task["status"]["status"],
                            "assignee": assignees,
                            "priority": priority_label,
                            "created_date": datetime.fromtimestamp(created_date).strftime("%Y-%m-%d %H:%M") if created_date else None,
                            "start_date": datetime.fromtimestamp(start_date).strftime("%Y-%m-%d") if start_date else None,
                            "due_date": datetime.fromtimestamp(due_date).strftime("%Y-%m-%d") if due_date else None,
                            "list": list_name,
                            "folder": folder_name,
                            "space": space_name,
                            "team": team_name
                        })

    return all_tasks


if __name__ == "__main__":
    tasks = get_all_tasks_with_subtasks()
    print(f"\n✅ {len(tasks)} tâches récupérées (avec subtasks, done, dates)\n")

    for task in tasks:
        prefix = "└─🧷" if task["type"] == "subtask" else "📌"
        print(f"{prefix} {task['task_name']} - {task['status']} - {task['list']} - {task['assignee']} - {task['priority']}")

    df = pd.DataFrame(tasks)
    df.to_excel("all_clickup_tasks_with_subtasks.xlsx", index=False)
    print("\n📁 Fichier exporté : all_clickup_tasks_with_subtasks.xlsx")

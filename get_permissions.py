import os
import json
import requests
from dotenv import load_dotenv
from mapping_users import get_users, extract_users


load_dotenv()

token = os.getenv("TOKEN")
org_id = os.getenv("ORGID")
queue = "COMMONTASKS"


def get_queues(token: str, org_id: str) -> list:
    headers = {"X-Cloud-Org-Id": f"{org_id}", "Authorization": f"OAuth {token}"}
    response = requests.get(f"https://api.tracker.yandex.net/v2/queues", headers=headers)
    elements = response.json()
    queues = []
    for element in elements:
        queues.append(element["key"])
    return queues


def get_permissions(token: str, org_id: str, queue: str) -> list:
    headers = {"X-Cloud-Org-Id": f"{org_id}", "Authorization": f"OAuth {token}"}
    response = requests.get(f"https://api.tracker.yandex.net/v2/queues/{queue}/permissions", headers=headers)
    elements = response.json()
    users_permission = []
    for permission, element in elements.items():
        if permission in ["read", "write", "create", "grant"] and element.get("users"):
            users_id = []
            for user_id in element["users"]:
                users_id.append(user_id["id"])
            users_permission.append({permission: users_id})
    return users_permission


def replace_userid_permissions(token: str, org_id: str, queue, filename):
    with open(filename, "r") as file:
        rows = file.readlines()
        old_users = []
        new_users = []
        for row in rows:
            old_users.append(row.split(" ")[0])
            new_users.append(row.split(" ")[1])

    headers = {
                "X-Cloud-Org-Id": f"{org_id}",
                "Authorization": f"OAuth {token}"
            }
    data = {
            "create": {"users": {"add": new_users, "remove": old_users}},
            "read": {"users": {"add": new_users, "remove": old_users}},
            "write": {"users": {"add": new_users, "remove": old_users}},
            "grant": {"users": {"add": new_users, "remove": old_users}}
        }
    
    response = requests.patch(
                                f"https://api.tracker.yandex.net/v2/queues/{queue}/permissions",
                                headers=headers,
                                data=json.dumps(data)
                                )
    print("OLD", old_users, "NEW", new_users)
    print(response.status_code)


queues = get_queues(token, org_id)
for queue in queues:
    permissions = get_permissions(token, org_id, queue)
    print(queue, permissions)

users = get_users(token, org_id)
old_users, new_users = extract_users(users)

replace_userid_permissions(token, org_id, "COMMONTASKS", "to.txt")

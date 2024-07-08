import os
import requests
from dotenv import load_dotenv


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


            
    # response_update = requests.patch(f"https://api.tracker.yandex.net/v2/queues/{queue}/permissions", headers=headers, data=data)

get_queues(token, org_id)
# get_permissions(token, org_id, queue)

import os
import json
import requests
from dotenv import load_dotenv
from mapping_users import get_users, extract_users


load_dotenv()

token = os.getenv("TOKEN")
org_id = os.getenv("ORGID")
# queue = "COMMONTASKS"


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


def replace_userid_permissions(
                                token: str,
                                org_id: str,
                                queue,
                                users_recall_permissions_read,
                                users_recall_permissions_write,
                                users_recall_permissions_create,
                                users_recall_permissions_grant,
                                users_give_permissions_read,
                                users_give_permissions_write,
                                users_give_permissions_create,
                                users_give_permissions_grant
                            ):
    headers = {
                "X-Cloud-Org-Id": f"{org_id}",
                "Authorization": f"OAuth {token}"
            }
    data = {
            "create": {"users": {"add": users_give_permissions_create, "remove": users_recall_permissions_create}},
            "read": {"users": {"add": users_give_permissions_read, "remove": users_recall_permissions_read}},
            "write": {"users": {"add": users_give_permissions_write, "remove": users_recall_permissions_write}},
            "grant": {"users": {"add": users_give_permissions_grant, "remove": users_recall_permissions_grant}}
        }
    
    response = requests.patch(
                                f"https://api.tracker.yandex.net/v2/queues/{queue}/permissions",
                                headers=headers,
                                data=json.dumps(data)
                                )
    # print("OLD", old_users, "NEW", new_users)
    # print(response.status_code)


queues = get_queues(token, org_id)

users = get_users(token, org_id)



queue = "COMMONTASKS"

permissions = get_permissions(token, org_id, queue)


users_recall_permissions_read = []
users_recall_permissions_write = []
users_recall_permissions_create = []
users_recall_permissions_grant = []

users_give_permissions_read = []
users_give_permissions_write = []
users_give_permissions_create = []
users_give_permissions_grant = []


with open("to.txt", "r") as file:
    rows = file.readlines()
    for permission in permissions:
        old_read_users = permission.get("read", [])
        old_write_users = permission.get("write", [])
        old_create_users = permission.get("create", [])
        old_grant_users = permission.get("grant", [])

        for row in rows:
            old_u = row.split(" ")[0]
            new_u = row.split(" ")[1]
            if old_u in old_read_users:
                users_recall_permissions_read.append(old_u)
                users_give_permissions_read.append(new_u)
            elif old_u in old_write_users:
                users_recall_permissions_write.append(old_u)
                users_give_permissions_write.append(new_u)
            elif old_u in old_create_users:
                users_recall_permissions_create.append(old_u)
                users_give_permissions_create.append(new_u)
            elif old_u in old_grant_users:
                users_recall_permissions_grant.append(old_u)
                users_give_permissions_grant.append(new_u)


replace_userid_permissions(
                            token,
                            org_id,
                            queue,
                            users_recall_permissions_read,
                            users_recall_permissions_write,
                            users_recall_permissions_create,
                            users_recall_permissions_grant,
                            users_give_permissions_read,
                            users_give_permissions_write,
                            users_give_permissions_create,
                            users_give_permissions_grant
                        )

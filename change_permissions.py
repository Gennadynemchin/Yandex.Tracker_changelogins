import os
import json
import requests
from dotenv import load_dotenv
from mapping_users import get_users


load_dotenv()


def get_queues(base_url: str, orgid: str, orgheader: str, token: str) -> list[str]:
    headers = {orgheader: orgid, "Authorization": token}
    response = requests.get(f"{base_url}/queues", headers=headers)
    response.raise_for_status()
    return [element["key"] for element in response.json()]


def get_permissions(
    base_url: str, orgid: str, orgheader: str, token: str, queue: str
) -> dict[str, list[str]]:
    headers = {orgheader: orgid, "Authorization": token}
    response = requests.get(f"{base_url}/queues/{queue}/permissions", headers=headers)
    response.raise_for_status()
    elements = response.json()
    return {
        permission: [user["id"] for user in element["users"]]
        for permission, element in elements.items()
        if permission in ["read", "write", "create", "grant"] and element.get("users")
    }


def replace_userid_permissions(
    base_url: str,
    orgid: str,
    orgheader: str,
    token: str,
    queue: str,
    users_recall: dict[str, list[str]],
    users_give: dict[str, list[str]],
) -> None:
    headers = {orgheader: orgid, "Authorization": token}
    data = {
        perm: {"users": {"add": users_give[perm], "remove": users_recall[perm]}}
        for perm in ["create", "read", "write", "grant"]
    }

    response = requests.patch(
        f"{base_url}/queues/{queue}/permissions", headers=headers, data=json.dumps(data)
    )
    response.raise_for_status()


def process_user_permissions(
    file_path: str, permissions: dict[str, list[str]]
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    users_recall = {perm: [] for perm in ["read", "write", "create", "grant"]}
    users_give = {perm: [] for perm in ["read", "write", "create", "grant"]}
    with open(file_path, "r") as file:
        for row in file:
            old_u = row.split(" ")[0]
            new_u = row.split(" ")[1]
            for perm in users_recall:
                if old_u in permissions.get(perm, []):
                    users_recall[perm].append(old_u)
                    users_give[perm].append(new_u)
    return users_recall, users_give


if __name__ == "__main__":
    TOKEN = os.getenv("TOKEN")
    ORG_ID = os.getenv("ORGID")
    ORGHEADER = os.getenv("ORGHEADER")
    BASEURL = os.getenv("BASEURL")
    DEFAULT_QUEUE = "COMMONTASKS"

    queues = get_queues()
    users = get_users(TOKEN, ORG_ID, ORGHEADER)
    permissions = get_permissions(BASEURL, ORG_ID, TOKEN, DEFAULT_QUEUE)
    users_recall, users_give = process_user_permissions("to.txt", permissions)
    replace_userid_permissions(
        BASEURL, ORG_ID, ORGHEADER, TOKEN, DEFAULT_QUEUE, users_recall, users_give
    )

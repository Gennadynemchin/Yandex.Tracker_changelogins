import json
import requests
from mapping_users import get_users
from settings import creds
from logger import logger


def get_queues(creds) -> list[str]:
    response = requests.get(f"{creds.baseurl}/queues", headers=creds.get_headers())
    response.raise_for_status()
    result = [element["key"] for element in response.json()]
    logger.info("%s", f"The following queues was found: {result}\n")
    return result


def get_permissions(creds, queue: str) -> dict[str, list[str]]:
    response = requests.get(
        f"{creds.baseurl}/queues/{queue}/permissions", headers=creds.get_headers()
    )
    response.raise_for_status()
    elements = response.json()
    logger.info("%s", f"Got permissions info: {elements}\n")
    return {
        permission: [user["id"] for user in element["users"]]
        for permission, element in elements.items()
        if permission in ["read", "write", "create", "grant"] and element.get("users")
    }


def replace_userid_permissions(
    creds,
    queue: str,
    users_recall: dict[str, list[str]],
    users_give: dict[str, list[str]],
) -> None:
    data = {
        perm: {"users": {"add": users_give[perm], "remove": users_recall[perm]}}
        for perm in ["create", "read", "write", "grant"]
    }
    logger.info("%s", f"The following data is ready to upload: {data}\n")
    response = requests.patch(
        f"{creds.baseurl}/queues/{queue}/permissions",
        headers=creds.get_headers(),
        data=json.dumps(data),
    )
    logger.info("%s", f"Server answered: {response.json()}\n")
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
    logger.info("%s", f"Got users for recall permissions: {users_recall}\n")
    logger.info("%s", f"Got users for give permissions: {users_give}\n")
    return users_recall, users_give


if __name__ == "__main__":
    DEFAULT_QUEUE = "COMMONTASKS"

    queues = get_queues(creds)
    users = get_users(creds)
    permissions = get_permissions(creds, DEFAULT_QUEUE)
    users_recall, users_give = process_user_permissions("to.txt", permissions)
    replace_userid_permissions(creds, DEFAULT_QUEUE, users_recall, users_give)

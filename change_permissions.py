import argparse
import json
import requests
from changelogins_bulk import get_list_from_file
from settings import creds
from logger import logger


def get_permissions(creds, queue: str) -> dict[str, list[str]] | None:
    response = requests.get(
        f"{creds.baseurl}/queues/{queue}/permissions", headers=creds.headers
    )
    if response.status_code == 403:
        logger.warning("Permission denied: %s", queue)
        return None
    response.raise_for_status()
    elements = response.json()
    logger.info("Got permissions info: %s", elements)
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
    logger.info("The following data is ready to upload: %s", data)
    response = requests.patch(
        f"{creds.baseurl}/queues/{queue}/permissions",
        headers=creds.headers,
        data=json.dumps(data),
    )
    response.raise_for_status()
    logger.info("Server answered: %s", response.json())



def process_user_permissions(
    file_path: str, permissions: dict[str, list[str]],
    remove_old_user: bool = True
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    users_recall = {perm: [] for perm in ["read", "write", "create", "grant"]}
    users_give = {perm: [] for perm in ["read", "write", "create", "grant"]}
    with open(file_path, "r") as file:
        for row in file:
            row = row.strip()
            if not row:
                continue
            parts = row.split(" ")
            if len(parts) < 2:
                continue
            old_u = parts[0]
            new_u = parts[1]
            for perm in users_recall:
                if old_u in permissions.get(perm, []):
                    if remove_old_user:
                        users_recall[perm].append(old_u)
                    users_give[perm].append(new_u)
    logger.info("Got users for recall permissions: %s", users_recall)
    logger.info("Got users for give permissions: %s", users_give)
    return users_recall, users_give


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Change permissions in queues Yandex Tracker")
    parser.add_argument(
        "--remove-old-user",
        action="store_true",
        help="Remove old user from permissions (default: keep old user)"
    )
    args = parser.parse_args()

    queues_list = get_list_from_file("queues.txt")

    for queue in queues_list:
        queue = queue.rstrip()
        permissions = get_permissions(creds, queue)
        if permissions is None:
            logger.error("Cannot proceed without permissions for queue %s", queue)
            continue
        users_recall, users_give = process_user_permissions("to.txt", permissions, remove_old_user=args.remove_old_user)
        replace_userid_permissions(creds, queue, users_recall, users_give)

import argparse
import json
import requests
from requests.exceptions import HTTPError
from settings import creds, PERMISSION_ROLES
from logger import logger


def get_all_components(crd) -> list:
    response = requests.get(
        f"{crd.baseurl}/components", headers=crd.headers
    )
    response.raise_for_status()
    elements = response.json()
    logger.info("Server answered: %s", elements)
    return [cmp.get("id") for cmp in elements]


def get_component_permissions(crd, component_id: str) -> dict | None:
    response = requests.get(
        f"{crd.baseurl}/components/{component_id}/access", headers=crd.headers
    )
    if response.status_code == 404:
        logger.warning("Component not found: %s", component_id)
        return None
    response.raise_for_status()
    elements = response.json()
    logger.info("Server answered: %s", elements)
    version = elements["version"]
    output_data = {}
    for element_name, element_value in elements.items():
        if element_name in PERMISSION_ROLES:
            output_data[element_name] = [user["id"] for user in element_value["users"]]
    output_data["version"] = version
    return output_data


def replace_component_permissions(permissions, remove_old_user: bool = True) -> dict:
    replaced_users = {}
    output_data = {}
    try:
        with open("to.txt", "r") as file:
            for row in file:
                row = row.strip()
                if not row:
                    continue
                parts = row.split(" ")
                if len(parts) < 2:
                    logger.warning("Invalid line format: %s", row)
                    continue
                old_u = parts[0]
                new_u = parts[1]
                for perm in PERMISSION_ROLES:
                    if old_u in permissions.get(perm, []) and new_u not in permissions.get(perm, []):
                        if remove_old_user:
                            permissions[perm].remove(old_u)
                        permissions[perm].append(new_u)
    except FileNotFoundError:
        logger.error("File not found: to.txt",)
        raise
    for perm in PERMISSION_ROLES:
        if perm in permissions:
            replaced_users[perm] = {"users": permissions[perm]}
    output_data["version"] = permissions["version"]
    output_data["data"] = replaced_users
    logger.info("Prepared data for replace permissions: %s", output_data)
    return output_data


def change_component_permissions(
    crd,
    component_id: str,
    permissions_details: dict,
):
    params = {"version": permissions_details["version"]}
    data = json.dumps(permissions_details["data"])
    logger.info(
        "Going to change permissions for component: %s with following users: %s", component_id, data
    )
    response = requests.patch(
        f"{crd.baseurl}/components/{component_id}/permissions",
        headers=crd.headers,
        data=data,
        params=params,
    )
    response.raise_for_status()
    logger.info("Server answered: %s", response.json())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Change component permissions in Yandex Tracker")
    parser.add_argument(
        "--remove-old-user",
        action="store_true",
        help="Remove old user from permissions (default: keep old user)"
    )
    args = parser.parse_args()

    all_components = get_all_components(creds)
    for component in all_components:
        try:
            permissions_data = get_component_permissions(creds, component)
            if permissions_data is None:
                continue
            new_permissions_data = replace_component_permissions(
                permissions_data, remove_old_user=args.remove_old_user
            )
            change_component_permissions(creds, component, new_permissions_data)
        except HTTPError:
            logger.exception("HTTP error occurred for component %s", component)
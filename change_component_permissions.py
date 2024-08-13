import json
import requests
from settings import creds
from logger import logger


def get_copmponent_permissions(creds, component_id: str) -> dict:
    headers = {creds.orgheader: creds.orgid, "Authorization": f"OAuth {creds.token}"}
    response = requests.get(
        f"{creds.baseurl}/components/{component_id}/access", headers=headers
    )
    response.raise_for_status()
    elements = response.json()
    logger.info("%s", f"Server answered: {elements}\n")
    permission_roles = ["create", "read", "writeNoAssign", "write", "grant"]
    version = elements["version"]
    output_data = {}
    for element_name, element_value in elements.items():
        if element_name in permission_roles:
            ids = []
            users = element_value["users"]
            for user in users:
                ids.append(user["id"])
            output_data[element_name] = ids
    output_data["version"] = version
    return output_data


def replace_component_permissions(file_path: str, permissions):
    component_permissions = ["create", "read", "writeNoAssign", "write", "grant"]
    replaced_users = {}
    output_data = {}

    with open(file_path, "r") as file:
        for row in file:
            old_u = row.split(" ")[0]
            new_u = row.split(" ")[1]
            for perm in component_permissions:
                if old_u in permissions.get(perm, []):
                    permissions[perm].remove(old_u)
                    permissions[perm].append(new_u)
                replaced_users[perm] = {"users": permissions[perm]}
    output_data["version"] = permissions["version"]
    output_data["data"] = replaced_users
    logger.info("%s", f"Prepared data for replace permissions: {output_data}\n")
    return output_data


def change_component_permissions(
    creds,
    component_id: str,
    permissions_details: dict,
):
    headers = {creds.orgheader: creds.orgid, "Authorization": f"OAuth {creds.token}"}
    params = {"version": permissions_details["version"]}
    data = json.dumps(permissions_details["data"])
    logger.info(
        "%s",
        f"Going to change permissions for component: {component_id} with following usaers: {data}\n",
    )
    response = requests.patch(
        f"{creds.baseurl}/components/{component_id}/permissions",
        headers=headers,
        data=data,
        params=params,
    )
    response.raise_for_status()
    logger.info("%s", f"Server answered: {response.json()}\n")


if __name__ == "__main__":
    COMPONENT_ID = "3"
    permissions_data = get_copmponent_permissions(creds, COMPONENT_ID)
    new_permissions_data = replace_component_permissions("to.txt", permissions_data)
    change_component_permissions(creds, COMPONENT_ID, new_permissions_data)

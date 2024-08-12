import os
import json
import requests
from dotenv import load_dotenv
from logger import logger


load_dotenv()


def get_copmponent_permissions(
    base_url: str, orgid: str, orgheader: str, token: str, component_id: str
) -> dict:
    headers = {orgheader: orgid, "Authorization": f"OAuth {token}"}
    response = requests.get(
        f"{base_url}/components/{component_id}/access", headers=headers
    )
    response.raise_for_status()
    elements = response.json()
    logger.info("%s", f"Server answered: {elements}")
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
    logger.info("%s", f"Prepared data for replace permissions: {output_data}")
    return output_data


def change_component_permissions(
    base_url: str,
    orgid: str,
    orgheader: str,
    token: str,
    component_id: str,
    permissions_details: dict,
):
    headers = {orgheader: orgid, "Authorization": f"OAuth {token}"}
    params = {"version": permissions_details["version"]}
    data = json.dumps(permissions_details["data"])
    logger.info(
        "%s",
        f"Going to change permissions for component: {component_id} with following usaers: {data}",
    )
    response = requests.patch(
        f"{base_url}/components/{component_id}/permissions",
        headers=headers,
        data=data,
        params=params,
    )
    response.raise_for_status()
    logger.info("%s", f"Server answered: {response.json()}")


if __name__ == "__main__":
    TOKEN = os.getenv("TOKEN")
    ORGID = os.getenv("ORGID")
    ORGHEADER = os.getenv("ORGHEADER")
    BASEURL = os.getenv("BASEURL")
    COMPONENT_ID = "3"
    permissions_data = get_copmponent_permissions(
        BASEURL, ORGID, ORGHEADER, TOKEN, COMPONENT_ID
    )
    new_permissions_data = replace_component_permissions("to.txt", permissions_data)
    change_component_permissions(
        BASEURL, ORGID, ORGHEADER, TOKEN, COMPONENT_ID, new_permissions_data
    )

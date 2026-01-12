import os
import json
import requests
from requests.exceptions import HTTPError
from typing import Dict, List, Set
from settings import creds
from logger import logger
from get_components import get_all_components


def get_entities(creds):
    params = {"fields": "entityStatus"} # delete then
    entity_types = ["project", "portfolio", "goal"]
    output_data = {}
    for entity in entity_types:
        response = requests.post(
            f"{creds.baseurl}/entities/{entity}/_search", headers=creds.headers, params=params
        )
        response.raise_for_status()
        elements = response.json()
        logger.info("%s", f"Server answered: {elements}\n")
        output_data[entity] = elements
    return output_data


def get_entities_permissions(creds, entity_type: str, entity_id: str):
    response = requests.get(
        f"{creds.v3url}/entities/{entity_type}/{entity_id}/extendedPermissions", headers=creds.headers
    )
    response.raise_for_status()
    elements = response.json()
    logger.info("%s", f"Server answered: {elements}\n")
    return elements


def parse_entities(data):
    parsed_entities = {}
    parsed_entities["project"] = [item["id"] for item in data.get("project", {}).get("values", [])]
    parsed_entities["portfolio"] = [item["id"] for item in data.get("portfolio", {}).get("values", [])]
    parsed_entities["goal"] = [item["id"] for item in data.get("goal", {}).get("values", [])]

    output_data = {}
    for entity_type, entities_id in parsed_entities.items():
        output_data[entity_type] = []
        for entity_id in entities_id:
            data_permissions = get_entities_permissions(creds, entity_type, entity_id)
            output_data[entity_type].append({"entity_id": entity_id, "permissions": data_permissions.get("acl")})
    logger.info("%s", f"parsed: {output_data}\n")
    return output_data


def add_entity_permissions(creds, entity_type, entity_id, permissions):
    permissions = {
                   "acl": permissions
                }
    print(permissions)
    response = requests.patch(
        f"{creds.v3url}/entities/{entity_type}/{entity_id}/extendedPermissions", headers=creds.headers, json=permissions
    )
    response.raise_for_status()
    elements = response.json()
    logger.info("%s", f"Server answered: {elements}\n")
    return elements


def transform_permissions_to_acl(data):
    result = []
    entity_types = ["project", "portfolio", "goal"]
    for entity_type in entity_types:
        entities = data.get(entity_type, [])
        for item in entities:
            entity_id = item.get("entity_id")
            permissions = item.get("permissions", {})
            if not entity_id:
                continue
            grant_user_ids = set()
            write_user_ids = set()
            read_user_ids = set()
            if "GRANT" in permissions:
                for user in permissions["GRANT"].get("users", []):
                    user_id = user.get("id")
                    if user_id:
                        grant_user_ids.add(user_id)
            if "WRITE" in permissions:
                for user in permissions["WRITE"].get("users", []):
                    user_id = user.get("id")
                    if user_id:
                        write_user_ids.add(user_id)
            if "READ" in permissions:
                for user in permissions["READ"].get("users", []):
                    user_id = user.get("id")
                    if user_id:
                        read_user_ids.add(user_id)
            # read_user_ids = grant_user_ids | write_user_ids  # Union
            write_user_ids_final = write_user_ids.copy()
            grant_user_ids_final = grant_user_ids.copy()
            read_user_ids_final = read_user_ids.copy()
            acl = {
                "grant": {
                    "READ": {"users": read_user_ids},
                    "WRITE": {"users": write_user_ids_final},
                    "GRANT": {"users": grant_user_ids_final}
                }
            }
            result.append({
                "entity_id": entity_id,
                "entity_type": entity_type,
                "acl": acl
            })
    return result


def replace_users_in_acl(summarized_permissions):
    if os.path.isfile("to.txt"):
        text_file = open("to.txt", "r")
        data = text_file.readlines()
        text_file.close()
        for line in data:
            line = line.partition("#")
            line = line[0]
            if (line.split(" " , 2)[1] != "") and (len(line.split(" " , 2)[1]) > 5):
                line.rstrip('\r\n')
                old_uid = line.split(" " , 2)[0]
                new_uid = line.split(" " , 2)[1]

    try:
        with open("to.txt", "r") as file:
            for line_num, line in enumerate(file, 1):
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) != 2:
                    print(f"Warning: Line {line_num} doesn't contain exactly 2 values: {line}")
                    continue
                old_user_id, new_user_id = parts
                for entity in summarized_permissions:
                    grant = entity["acl"]["grant"]
                    for permission in ["READ", "WRITE", "GRANT"]:
                        users_list = grant[permission]["users"]
                        grant[permission]["users"] = [
                            new_user_id if user == old_user_id else user
                            for user in users_list
                        ]
    except FileNotFoundError:
        print(f"Error: File 'to.txt' not found.")
        return []
    except Exception as e:
        print(f"Error reading file: {e}")
        return []

    return summarized_permissions




entities = get_entities(creds)
parsed_entities = parse_entities(entities)
summarized_permissions = transform_permissions_to_acl(parsed_entities)
replaced_users_in_permissions = replace_users_in_acl(summarized_permissions)

for entity in replaced_users_in_permissions:
    entity_id = entity.get("entity_id")
    entity_type = entity.get("entity_type")
    permissions = entity.get("acl")
    add_entity_permissions(creds, entity_type, entity_id, permissions)

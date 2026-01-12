import os
import json
import requests
from requests.exceptions import HTTPError
from typing import Dict, List, Set
from settings import creds
from logger import logger
from get_components import get_all_components


def get_entities_data(creds) -> dict:
    params = {"fields": "entityStatus"}
    entities_type = ["project", "portfolio", "goal"]
    output_data = {}
    for entity in entities_type:
        response = requests.post(
            f"{creds.baseurl}/entities/{entity}/_search", headers=creds.headers, params=params
        )
        response.raise_for_status()
        elements = response.json()
        logger.info("%s", f"Server answered: {elements}\n")
        output_data[entity] = elements
    return output_data


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
    return output_data


def get_entities_permissions(creds, entity_type: str, entity_id: str):
    response = requests.get(
        f"{creds.v3url}/entities/{entity_type}/{entity_id}/extendedPermissions", headers=creds.headers
    )
    response.raise_for_status()
    elements = response.json()
    logger.info("%s", f"Server answered: {elements}\n")
    return elements


def add_entity_permissions(creds, entity_type, entity_id, permissions):
    permissions = {
                   "acl": permissions
                }
    response = requests.patch(
        f"{creds.v3url}/entities/{entity_type}/{entity_id}/extendedPermissions", headers=creds.headers, json=permissions
    )
    response.raise_for_status()
    elements = response.json()


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
            read_user_ids = grant_user_ids | write_user_ids  # Union
            write_user_ids_final = write_user_ids.copy()
            grant_user_ids_final = grant_user_ids.copy()
            acl = {
                "grant": {
                    "READ": {"users": sorted(read_user_ids)},
                    "WRITE": {"users": sorted(write_user_ids_final)},
                    "GRANT": {"users": sorted(grant_user_ids_final)}
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
                print(line.rstrip('\r\n'))
                old_uid = line.split(" " , 2)[0]
                new_uid = line.split(" " , 2)[1]
                print(f"Old: {old_uid}, New: {new_uid}")

                for entity in summarized_permissions:
                    grant = entity["acl"]["grant"]
                    for permission in ["READ", "WRITE", "GRANT"]:
                        users_list = grant[permission]["users"]
                        grant[permission]["users"] = [
                            new_uid if user == old_uid else user
                            for user in users_list
                        ]
    return summarized_permissions




entities_data = get_entities_data(creds)
parsed_entities = parse_entities(entities_data)
summarized_permissions = transform_permissions_to_acl(parsed_entities)
replaced_users_in_permissions = replace_users_in_acl(summarized_permissions)



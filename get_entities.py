import requests
from settings import creds
from logger import logger


def get_entities(crd):
    ent_types = ["project", "portfolio", "goal"]
    output_data = {}
    for ent in ent_types:
        response = requests.post(
            f"{crd.baseurl}/entities/{ent}/_search", headers=crd.headers
        )
        response.raise_for_status()
        elements = response.json()
        logger.info("Server answered: %s", elements)
        output_data[ent] = elements
    return output_data


def get_entities_permissions(crd, ent_type: str, ent_id: str):
    response = requests.get(
        f"{crd.v3url}/entities/{ent_type}/{ent_id}/extendedPermissions", headers=crd.headers
    )
    response.raise_for_status()
    elements = response.json()
    logger.info("Server answered: %s", elements)
    return elements


def parse_entities(crd, data):
    parsed_ent = {"project": [item["id"] for item in data.get("project", {}).get("values", [])],
                  "portfolio": [item["id"] for item in data.get("portfolio", {}).get("values", [])],
                  "goal": [item["id"] for item in data.get("goal", {}).get("values", [])]}

    output_data = {}
    for ent_type, ids in parsed_ent.items():
        output_data[ent_type] = []
        for ent_id in ids:
            data_permissions = get_entities_permissions(crd, ent_type, ent_id)
            output_data[ent_type].append({"entity_id": ent_id, "permissions": data_permissions.get("acl")})
    logger.info("parsed: %s", output_data)
    return output_data


def add_entity_permissions(crd, ent_type, ent_id, perms):
    data = {
                   "acl": perms
                }
    response = requests.patch(
        f"{crd.v3url}/entities/{ent_type}/{ent_id}/extendedPermissions", headers=crd.headers, json=data
    )
    response.raise_for_status()
    elements = response.json()
    logger.info("Server answered: %s", elements)
    return elements


def transform_permissions_to_acl(data) -> list:
    result = []
    ent_types = ["project", "portfolio", "goal"]
    for ent_type in ent_types:
        ents = data.get(ent_type, [])
        for item in ents:
            ent_id = item.get("entity_id")
            perms = item.get("permissions", {})
            if not ent_id:
                continue
            grant_user_ids = set()
            write_user_ids = set()
            read_user_ids = set()
            if "GRANT" in perms:
                for user in perms["GRANT"].get("users", []):
                    user_id = user.get("id")
                    if user_id:
                        grant_user_ids.add(user_id)
            if "WRITE" in perms:
                for user in perms["WRITE"].get("users", []):
                    user_id = user.get("id")
                    if user_id:
                        write_user_ids.add(user_id)
            if "READ" in perms:
                for user in perms["READ"].get("users", []):
                    user_id = user.get("id")
                    if user_id:
                        read_user_ids.add(user_id)
            acl = {
                "grant": {
                    "READ": {"users": list(read_user_ids)},
                    "WRITE": {"users": list(write_user_ids)},
                    "GRANT": {"users": list(grant_user_ids)}
                }
            }
            result.append({
                "entity_id": ent_id,
                "entity_type": ent_type,
                "acl": acl
            })
    return result


def replace_users_in_acl(summarized_perms):
    try:
        with open("to.txt", "r") as file:
            for line_num, line in enumerate(file, 1):
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) != 2:
                    logger.warning("Line %d doesn't contain exactly 2 values: %s", line_num, line)
                    continue
                old_user_id, new_user_id = parts
                for ent in summarized_perms:
                    grant = ent["acl"]["grant"]
                    for permission in ["READ", "WRITE", "GRANT"]:
                        users_list = grant[permission]["users"]
                        grant[permission]["users"] = [
                            new_user_id if user == old_user_id else user
                            for user in users_list
                        ]
    except FileNotFoundError:
        logger.error("Error: File 'to.txt' not found.")
        return []
    except Exception as e:
        logger.error("Error reading file: %s", e)
        return []
    return summarized_perms


if __name__ == "__main__":
    try:
        entities = get_entities(creds)
        parsed_entities = parse_entities(creds, entities)
        summarized_permissions = transform_permissions_to_acl(parsed_entities)
        replaced_users_in_permissions = replace_users_in_acl(summarized_permissions)

        if not replaced_users_in_permissions:
            logger.warning("No permissions to update. Exiting.")
        else:
            for entity in replaced_users_in_permissions:
                entity_id = entity.get("entity_id")
                entity_type = entity.get("entity_type")
                permissions = entity.get("acl")
                add_entity_permissions(creds, entity_type, entity_id, permissions)
            logger.info("All permissions updated successfully.")

    except requests.exceptions.HTTPError as err:
        logger.error("HTTP error occurred: %s", err)
    except requests.exceptions.ConnectionError:
        logger.error("Connection error. Check your network or API URL.")
    except requests.exceptions.Timeout:
        logger.error("Request timed out.")
    except Exception as err:
        logger.error("Unexpected error: %s", err)
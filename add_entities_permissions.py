import requests
from dotenv import load_dotenv
from settings import creds, ENTITY_TYPES
from logger import logger


def get_entities(crd):
    output_data = {}
    for ent in ENTITY_TYPES:
        response = requests.post(
            f"{crd.baseurl}/entities/{ent}/_search", headers=crd.headers
        )
        response.raise_for_status()
        elements = response.json()
        logger.info("Server answered: %s", elements)
        output_data[ent] = elements
        logger.info(
            "Fetched %s: %d items", ent, len(elements.get("values", []))
        )
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
    parsed_ent = {
        ent_type: [item["id"] for item in data.get(ent_type, {}).get("values", [])]
        for ent_type in ENTITY_TYPES
    }

    output_data = {}
    for ent_type, ids in parsed_ent.items():
        logger.info("Processing %s: %d entities", ent_type, len(ids))
        output_data[ent_type] = []
        for ent_id in ids:
            data_permissions = get_entities_permissions(crd, ent_type, ent_id)
            output_data[ent_type].append({"entity_id": ent_id, "permissions": data_permissions.get("acl")})
            logger.debug("Processed permissions for %s/%s", ent_type, ent_id)
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
    for ent_type in ENTITY_TYPES:
        ents = data.get(ent_type, [])
        for item in ents:
            ent_id = item.get("entity_id")
            perms = item.get("permissions") or {}
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
        with open("to.txt", "r", encoding="utf-8") as file:
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
    load_dotenv()
    try:
        logger.info("Starting permissions sync...")
        logger.info("Fetching entities...")

        entities = get_entities(creds)
        logger.info("Parsing permissions...")

        parsed_entities = parse_entities(creds, entities)
        logger.info("Transforming to ACL format...")

        summarized_permissions = transform_permissions_to_acl(parsed_entities)
        logger.info("Applying user replacements from to.txt...")

        replaced_users_in_permissions = replace_users_in_acl(summarized_permissions)
        logger.info("Found %d entities to process", len(replaced_users_in_permissions))

        if not replaced_users_in_permissions:
            logger.warning("No permissions to update. Exiting.")
        else:
            success_count = 0
            error_count = 0

            for entity in replaced_users_in_permissions:
                entity_id = entity.get("entity_id")
                entity_type = entity.get("entity_type")
                permissions = entity.get("acl")
                if not creds.dryrun:
                    try:
                        add_entity_permissions(creds, entity_type, entity_id, permissions)
                        success_count += 1
                        logger.info("Updated %d/%d: %s/%s",
                                    success_count+error_count,
                                    len(replaced_users_in_permissions),
                                    entity_type, entity_id)
                    except requests.exceptions.HTTPError as e:
                        logger.error("Error updating permissions: %s/%s: %s", entity_type, entity_id, e)
                        error_count += 1
                else:
                    success_count += 1
                    logger.info("[DRY RUN] Would update %s/%s", entity_type, entity_id)

            logger.info("=" * 40)
            if creds.dryrun:
                logger.info("[DRY RUN] Would update %d entities", success_count)
            else:
                logger.info("Completed: %d success, %d errors", success_count, error_count)

    except requests.exceptions.HTTPError as err:
        logger.error("HTTP error occurred: %s", err)
    except requests.exceptions.ConnectionError:
        logger.error("Connection error. Check your network or API URL.")
    except requests.exceptions.Timeout:
        logger.error("Request timed out.")
    except Exception as err:
        logger.error("Unexpected error: %s", err)
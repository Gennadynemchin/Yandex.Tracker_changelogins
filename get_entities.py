import json
import requests
from requests.exceptions import HTTPError
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
    # print(json.dumps(output_data, indent=2))
    return output_data


def parse_entities(data):
    result = {}
    result["project"] = [item["id"] for item in data.get("project", {}).get("values", [])]
    result["portfolio"] = [item["id"] for item in data.get("portfolio", {}).get("values", [])]
    result["goal"] = [item["id"] for item in data.get("goal", {}).get("values", [])]
    return result


def get_entities_permissions(creds, entity_type: str, entity_id: str) -> list:
    response = requests.get(
        f"{creds.v3url}/entities/{entity_type}/{entity_id}/extendedPermissions", headers=creds.headers
    )
    response.raise_for_status()
    elements = response.json()
    logger.info("%s", f"Server answered: {elements}\n")



entities_data = get_entities_data(creds)
parsed_entities = parse_entities(entities_data)

for entity_type, entities_id in parsed_entities.items():
    for entity_id in entities_id:
        print(f"{entity_type} {entity_id}")
        get_entities_permissions(creds, entity_type, entity_id)

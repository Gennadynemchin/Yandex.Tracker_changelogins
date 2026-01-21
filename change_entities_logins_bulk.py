import json
import requests
from typing import List, Optional, Dict, Any, Tuple
from logger import logger
from settings import creds
from changelogins_bulk import get_list_from_file


SINGLE_VALUE_FIELDS = ["author", "createdBy", "lead"]
LIST_FIELDS = ["teamUsers", "clients", "followers"]


class EntityUserManager:

    def __init__(self, credentials):
        self.creds = credentials

    def search_entities(
        self, filter_field: str, entity_type: str, user_id: str, per_page: int = 100
    ) -> List[List[str]]:
        all_ids = []
        current_ids = []
        current_page = 1
        url = f"{self.creds.v3url}/entities/{entity_type}/_search"
        headers = self.creds.headers
        filter_params = {filter_field: user_id}
        data = json.dumps({"filter": filter_params})
        logger.info("Filter params prepared: %s", filter_params)

        try:
            while True:
                params = {"perPage": per_page, "page": current_page}
                response = requests.post(
                    url, params=params, headers=headers, data=data, timeout=30
                )
                response.raise_for_status()

                result = response.json()
                logger.info("Server answered: %s", result)
                all_pages = result.get("pages", 1)
                entities = result.get("values", [])

                for entity in entities:
                    entity_id = entity.get("id")
                    if not entity_id:
                        logger.warning("Entity without ID: %s", entity)
                        continue
                    if len(current_ids) == 10000:
                        all_ids.append(current_ids)
                        current_ids = []
                    current_ids.append(entity_id)

                if current_page >= all_pages:
                    if current_ids:
                        all_ids.append(current_ids)
                    break
                current_page += 1
        except requests.exceptions.HTTPError as e:
            logger.error(
                "HTTP error during search %s/%s: %s", entity_type, filter_field, e
            )
            if hasattr(e, 'response') and e.response is not None:
                logger.error("Response status: %s", e.response.status_code)
                logger.error("Response body: %s", e.response.text)
        except requests.exceptions.ConnectionError:
            logger.error(
                "Connection error during search %s/%s", entity_type, filter_field
            )
        except requests.exceptions.Timeout:
            logger.error("Timeout during search %s/%s", entity_type, filter_field)
        except Exception as e:
            logger.error(
                "Unexpected error during search %s/%s: %s", entity_type, filter_field, e
            )
        logger.info("Ids returned: %s", all_ids)
        return all_ids

    def update_single_field(
        self, field: str, user_id: str, entity_type: str, entity_ids: list
    ) -> Optional[Dict[str, Any]]:
        url = f"{self.creds.v3url}/entities/{entity_type}/bulkchange/_update"
        data = json.dumps(
            {"metaEntities": entity_ids, "values": {"fields": {field: user_id}}}
        )

        try:
            response = requests.post(
                url, headers=self.creds.headers, data=data, timeout=30
            )
            response.raise_for_status()
            response_data = response.json()
            logger.info(
                "Updated %s/%s for %d entities: %s",
                entity_type,
                field,
                len(entity_ids),
                response_data,
            )
            return response_data
        except requests.exceptions.HTTPError as e:
            logger.error("HTTP error updating %s/%s: %s", entity_type, field, e)
            if hasattr(e, 'response') and e.response is not None:
                logger.error("Response status: %s", e.response.status_code)
                logger.error("Response body: %s", e.response.text)
        except requests.exceptions.ConnectionError:
            logger.error("Connection error updating %s/%s", entity_type, field)
        except requests.exceptions.Timeout:
            logger.error("Timeout updating %s/%s", entity_type, field)
        except Exception as e:
            logger.error("Unexpected error updating %s/%s: %s", entity_type, field, e)
        return None

    def update_list_field(
        self,
        field: str,
        old_user_id: str,
        new_user_id: str,
        entity_type: str,
        entity_ids: list,
    ) -> Tuple[Optional[Dict], Optional[Dict]]:
        url = f"{self.creds.v3url}/entities/{entity_type}/bulkchange/_update"

        add_data = json.dumps(
            {
                "metaEntities": entity_ids,
                "values": {"fields": {field: {"add": [new_user_id]}}},
            }
        )

        add_result = None
        remove_result = None

        try:
            response = requests.post(
                url, headers=self.creds.headers, data=add_data, timeout=30
            )
            response.raise_for_status()
            add_result = response.json()
            logger.info(
                "Added user to %s/%s for %d entities: %s",
                entity_type,
                field,
                len(entity_ids),
                add_result,
            )
        except requests.exceptions.HTTPError as e:
            logger.error("HTTP error adding user to %s/%s: %s", entity_type, field, e)
            if hasattr(e, 'response') and e.response is not None:
                logger.error("Response status: %s", e.response.status_code)
                logger.error("Response body: %s", e.response.text)
            return None, None
        except requests.exceptions.ConnectionError:
            logger.error("Connection error adding user to %s/%s", entity_type, field)
            return None, None
        except requests.exceptions.Timeout:
            logger.error("Timeout adding user to %s/%s", entity_type, field)
            return None, None
        except Exception as e:
            logger.error(
                "Unexpected error adding user to %s/%s: %s", entity_type, field, e
            )
            return None, None

        remove_data = json.dumps(
            {
                "metaEntities": entity_ids,
                "values": {"fields": {field: {"remove": [old_user_id]}}},
            }
        )

        try:
            response = requests.post(
                url, headers=self.creds.headers, data=remove_data, timeout=30
            )
            response.raise_for_status()
            remove_result = response.json()
            logger.info(
                "Removed user from %s/%s for %d entities: %s",
                entity_type,
                field,
                len(entity_ids),
                remove_result,
            )
        except requests.exceptions.HTTPError as e:
            logger.error(
                "HTTP error removing user from %s/%s: %s", entity_type, field, e
            )
            if hasattr(e, 'response') and e.response is not None:
                logger.error("Response status: %s", e.response.status_code)
                logger.error("Response body: %s", e.response.text)
        except requests.exceptions.ConnectionError:
            logger.error(
                "Connection error removing user from %s/%s", entity_type, field
            )
        except requests.exceptions.Timeout:
            logger.error("Timeout removing user from %s/%s", entity_type, field)
        except Exception as e:
            logger.error(
                "Unexpected error removing user from %s/%s: %s", entity_type, field, e
            )
        logger.info("Add/remove completed: %s, %s", add_result, remove_result)
        return add_result, remove_result


if __name__ == "__main__":
    entity_types = ["project", "portfolio", "goal"]
    filter_fields = SINGLE_VALUE_FIELDS + LIST_FIELDS
    users_list = get_list_from_file("to.txt")

    manager = EntityUserManager(creds)

    success_count = 0
    error_count = 0

    logger.info("=" * 50)
    logger.info("Starting entity logins bulk change...")
    logger.info("Entity types: %s", entity_types)
    logger.info("Fields to process: %s", filter_fields)
    logger.info("Users to process: %d", len(users_list))
    logger.info("=" * 50)

    for user_line in users_list:
        user = user_line.strip()
        if not user:
            continue

        parts = user.split()
        if len(parts) != 2:
            logger.warning("Invalid line format (expected 2 values): %s", user)
            continue

        old_usr_id, new_usr_id = parts
        if not old_usr_id or not new_usr_id:
            logger.warning("Empty user ID: %s", user)
            continue

        logger.info("-" * 40)
        logger.info("Processing user: %s --> %s", old_usr_id, new_usr_id)

        for ent_type in entity_types:
            for fld in filter_fields:
                try:
                    entity_batches = manager.search_entities(
                        fld, ent_type, old_usr_id, per_page=100
                    )

                    if not entity_batches or not any(entity_batches):
                        logger.debug(
                            "No entities found for %s/%s with user %s",
                            ent_type,
                            fld,
                            old_usr_id,
                        )
                        continue

                    total_entities = sum(len(batch) for batch in entity_batches)
                    logger.info(
                        "Found %d %s(s) with %s=%s",
                        total_entities,
                        ent_type,
                        fld,
                        old_usr_id,
                    )

                    for batch in entity_batches:
                        if not batch:
                            continue

                        logger.info(
                            "Updating batch of %d %s(s) for field %s...",
                            len(batch),
                            ent_type,
                            fld,
                        )

                        if fld in SINGLE_VALUE_FIELDS:
                            res = manager.update_single_field(
                                fld, new_usr_id, ent_type, batch
                            )
                            if res:
                                success_count += len(batch)
                            else:
                                error_count += len(batch)
                        else:
                            add_res, remove_res = manager.update_list_field(
                                fld, old_usr_id, new_usr_id, ent_type, batch
                            )
                            if add_res:
                                if remove_res:
                                    success_count += len(batch)
                                    logger.info(
                                        "Full update completed for %d entities",
                                        len(batch),
                                    )
                                    logger.info("add_res log: %s", add_res)
                                    logger.info("remove_res log: %s", remove_res)
                                else:
                                    logger.warning(
                                        "Added new user but failed to remove old user for %d entities",
                                        len(batch),
                                    )
                                    logger.info("add_res log (no remove_res log): %s", add_res)
                                    error_count += len(batch)
                            else:
                                error_count += len(batch)
                except Exception as err:
                    logger.error(
                        "Unexpected error processing %s/%s: %s", ent_type, fld, err
                    )

    logger.info("=" * 50)
    logger.info("Completed: %d success, %d errors", success_count, error_count)
    logger.info("=" * 50)

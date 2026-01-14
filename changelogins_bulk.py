import sys
import json
import requests
from logger import logger
from settings import creds


def get_list_from_file(file):
    try:
        with open(file, "r") as saved_list:
            context = saved_list.readlines()
            return context
    except FileNotFoundError:
        logger.error("%s", f"File {file} has not been found")
        sys.exit(0)


def assignee_search(creds, filter: str, queue: str, old_user_id: str, perPage: int) -> list:
    all_keys = []
    current_keys = []
    currentPage = 1
    url = f"{creds.baseurl}/issues/_search"
    headers = creds.headers
    filter =  {filter: old_user_id, "queue": queue}
    data = json.dumps({"filter": filter})

    while True:
        params = {"perPage": perPage, "page": currentPage}
        response = requests.post(url, params=params, headers=headers, data=data)
        response.raise_for_status()
        allPages = int(response.headers["X-Total-Pages"])
        issues = response.json()
        for issue in issues:
            if len(current_keys) == 10000:
                all_keys.append(current_keys)
                current_keys = []
            current_keys.append(issue["key"])
        if currentPage >= allPages:
            if current_keys:
                all_keys.append(current_keys)
            break
        currentPage += 1
    return all_keys


def assignee_update(creds, filter: str, new_user_id: str, issues: list):
    url = f"{creds.baseurl}/bulkchange/_update"
    data = json.dumps({"issues": issues, "values": {filter: new_user_id}})
    response = requests.post(url, headers=creds.headers, data=data)
    response.raise_for_status()
    response_data = response.json()
    logger.info("%s", f"Server answered: {response_data}")
    return response_data


if __name__ == "__main__":
    perPage = 100
    filters = ["assignee", "createdBy", "followers"]
    queues_list = get_list_from_file("queues.txt")
    users_list = get_list_from_file("to.txt")

    for queue in queues_list:
        queue = queue.rstrip()
        for user in users_list:
            old_user_id = user.split(" ")[0]
            new_user_id = user.split(" ")[1]
            for filter in filters:
                all_issues = assignee_search(creds, filter, queue, old_user_id, perPage)
                for issues in all_issues:
                    logger.info("%s", f"Found {len(issues)} tasks")
                    logger.info(
                        "%s",
                        f"Going to update {filter} role for user {old_user_id}-->{new_user_id} in following issues: {issues}",
                    )
                    assignee_update(creds, filter, new_user_id, issues)

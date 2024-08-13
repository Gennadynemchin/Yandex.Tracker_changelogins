import sys
import json
import requests
from settings import creds
from logger import logger


def get_users_list(filename: str) -> None:
    try:
        with open(filename, "r") as users_list:
            context = users_list.readlines()
            return context
    except FileNotFoundError:
        logger.error("%s", f"File {filename} has not been found\n")
        sys.exit(0)


def assignee_search(creds, perPage: int, filter: dict) -> list:
    all_keys = []
    current_keys = []
    currentPage = 1
    url = f"{creds.baseurl}/issues/_search"
    data = json.dumps({"filter": filter})

    while True:
        params = {"perPage": perPage, "page": currentPage}
        response = requests.post(url, params=params, headers=creds.get_headers(), data=data)
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


def assignee_update(
    creds,
    filter: str,
    new_user_id: str,
    issues: list,
):
    url = f"{creds.baseurl}/bulkchange/_update"
    data = json.dumps({"issues": issues, "values": {filter: new_user_id}})
    response = requests.post(url, headers=creds.get_headers(), data=data)
    response.raise_for_status()
    response_data = response.json()
    logger.info("%s", f"Server answered: {response_data}\n")
    return response_data


if __name__ == "__main__":
    perPage = 1000
    user_roles = ["assignee", "createdBy", "followers"]
    users_list = get_users_list("to.txt")

    for user in users_list:
        old_user_id = user.split(" ")[0]
        new_user_id = user.split(" ")[1]

        for role in user_roles:
            filter = {role: old_user_id, "queue": ["COMMONTASKS"]}
            all_issues = assignee_search(creds, perPage, filter)
            for issues in all_issues:
                logger.info("%s", f"Found {len(issues)} tasks\n")
                logger.info(
                    "%s",
                    f"Going to update {filter} role for user {old_user_id}-->{new_user_id} in following issues: {issues}\n",
                )
                assignee_update(creds, filter, new_user_id, issues)

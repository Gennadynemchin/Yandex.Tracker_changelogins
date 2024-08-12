import os
import sys
import json
import requests
from dotenv import load_dotenv
from logger import logger


load_dotenv()


def get_users_list(filename: str) -> None:
    try:
        with open(filename, "r") as users_list:
            context = users_list.readlines()
            return context
    except FileNotFoundError:
        logger.error("%s", f"File {filename} has not been found")
        sys.exit(0)


def assignee_search(
    base_url: str, orgid: str, orgheader: str, token: str, perPage: int, filter: dict
) -> list:
    all_keys = []
    current_keys = []
    currentPage = 1
    url = f"{base_url}/issues/_search"
    token = f"OAuth {token}"
    headers = {orgheader: orgid, "Authorization": token}
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


def assignee_update(
    base_url: str,
    orgid: str,
    orgheader: str,
    token: str,
    filter: str,
    new_user_id: str,
    issues: list,
):
    url = f"{base_url}/bulkchange/_update"
    token = f"OAuth {token}"
    headers = {orgheader: orgid, "Authorization": token}
    data = json.dumps({"issues": issues, "values": {filter: new_user_id}})
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    response_data = response.json()
    logger.info("%s", f"Server answered: {response_data}")
    return response_data


if __name__ == "__main__":
    BASEURL = os.getenv("BASEURL")
    ORGID = os.getenv("ORGID")
    TOKEN = os.getenv("TOKEN")
    ORGHEADER = os.getenv("ORGHEADER")
    perPage = 1000
    user_roles = ["assignee", "createdBy", "followers"]
    users_list = get_users_list("to.txt")

    for user in users_list:
        old_user_id = user.split(" ")[0]
        new_user_id = user.split(" ")[1]

        for role in user_roles:
            filter = {role: old_user_id, "queue": ["COMMONTASKS"]}
            all_issues = assignee_search(
                BASEURL, ORGID, ORGHEADER, TOKEN, perPage, filter
            )
            for issues in all_issues:
                logger.info("%s", f"Found {len(issues)} tasks")
                logger.info(
                    "%s",
                    f"Going to update {filter} role for user {old_user_id}-->{new_user_id} in following issues: {issues}",
                )
                assignee_update(BASEURL, ORGID, TOKEN, filter, new_user_id, issues)

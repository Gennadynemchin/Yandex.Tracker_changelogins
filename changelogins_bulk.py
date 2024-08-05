import os
import json
import requests
from dotenv import load_dotenv
from logging import getLogger, basicConfig, FileHandler, StreamHandler, INFO


load_dotenv()

logger = getLogger(__name__)
FORMAT = "%(asctime)s : %(name)s : %(levelname)s : %(message)s"
file_handler = FileHandler("data.log")
file_handler.setLevel(INFO)
stream = StreamHandler()
stream.setLevel(INFO)
basicConfig(level=INFO, format=FORMAT, handlers=[file_handler, stream])


def get_users_list(file):
    with open(file, "r") as users_list:
        return users_list.readlines()


def assignee_search(
    orgid: str, token: str, filter: str, old_user_id: str, perPage: int
) -> list:
    all_keys = []
    current_keys = []
    currentPage = 1
    url = "https://api.tracker.yandex.net/v2/issues/_search"
    token = f"OAuth {token}"
    headers = {"X-Cloud-Org-ID": orgid, "Authorization": token}
    data = json.dumps({"filter": {filter: old_user_id}})

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
    orgid: str, token: str, filter: str, new_user_id: str, issues: list
):
    url = "https://api.tracker.yandex.net/v2/bulkchange/_update"
    token = f"OAuth {token}"
    headers = {"X-Cloud-Org-ID": orgid, "Authorization": token}
    data = json.dumps({"issues": issues, "values": {filter: new_user_id}})
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    response_data = response.json()
    logger.info("%s", f"Server answered: {response_data}")
    return response_data


if __name__ == "__main__":
    orgid = os.getenv("ORGID")
    token = os.getenv("TOKEN")
    perPage = 10
    filters = ["assignee", "createdBy", "followers"]
    users_list = get_users_list("to.txt")
    
    for user in users_list:
        old_user_id = user.split(" ")[0]
        new_user_id = user.split(" ")[1]

        for filter in filters:
            all_issues = assignee_search(orgid, token, filter, old_user_id, perPage)
            for issues in all_issues:
                logger.info("%s", f"Found {len(issues)} tasks")
                logger.info("%s", f"Going to update {filter} role for user {old_user_id}-->{new_user_id} in following issues: {issues}")
                assignee_update(orgid, token, filter, new_user_id, issues)

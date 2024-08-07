import os
import requests
import json
from dotenv import load_dotenv
from time import time


load_dotenv()


def create_issue(token, org_id):
    current_timestamp = time()
    data = json.dumps({
    "queue": "COMMONTASKS",
    "summary": f"AutoCreatedIssue-{current_timestamp}",
    "type": "task",
    "assignee": "8000000000000004"
})
    url = "https://api.tracker.yandex.net/v2/issues"
    headers = {"X-Cloud-Org-Id": f"{org_id}", "Authorization": f"OAuth {token}"}
    response = requests.post(url, headers=headers, data=data)
    return response.json()


token = os.getenv("TOKEN")
org_id = os.getenv("ORGID")

for x in range(1, 11):
    create_issue(token, org_id)
    print(x)

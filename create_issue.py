import requests
import json
from settings import creds
from time import time
from faker import Faker


fake = Faker()


def create_issue(creds, assignee):
    current_timestamp = time()
    data = json.dumps({
    "queue": creds.queue,
    "summary": f"AutoCreatedIssue-{current_timestamp}",
    "type": "task",
    "assignee": assignee,
    "description": fake.text()
})
    url = f"{creds.baseurl}/issues"
    response = requests.post(url, headers=creds.headers, data=data)
    return response.json()

for x in range(1, 11):
    create_issue(creds, "gnemchin")
    print(x)

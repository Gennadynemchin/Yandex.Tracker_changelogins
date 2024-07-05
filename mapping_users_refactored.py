import os
import requests
from dotenv import load_dotenv


load_dotenv()

token = os.getenv("TOKEN")
org_id = os.getenv("ORGID")


def get_users(token, org_id):
    headers = {"X-Cloud-Org-Id": f"{org_id}", "Authorization": f"OAuth {token}"}
    print(headers)
    response = requests.get("https://api.tracker.yandex.net/v2/users", headers=headers)
    elements = response.json()
    return elements


def extract_users(elements):
    cloud_users = []
    directory_users = []
    
    for element in elements:
        try:
            user_dict = {
                "id": element["uid"],
                "email": element["email"],
                "dismissed": element["dismissed"],
                "sources": element["sources"]
            }

            if len(user_dict["sources"]) == 1:
                source = user_dict["sources"][0]
                if source == "cloud":
                    cloud_users.append(user_dict)
                elif source == "directory":
                    directory_users.append(user_dict)

        except KeyError as e:
            missing_key = e.args[0]
            print(f"User {element.get('email', 'unknown')} doesn't have '{missing_key}' element")

    return cloud_users, directory_users


def match_and_write_to_file(cloud_users, directory_lookup, filename="to.txt"):
    with open(filename, "w") as file:
        for cloud_user in cloud_users:
            email = cloud_user['email']
            if email in directory_lookup:
                directory_user = directory_lookup[email]
                print(cloud_user['id'], directory_user['id'], directory_user['email'])
                file.write(f"{cloud_user['id']} {directory_user['id']} #\n")


def process_users(elements):
    cloud_users, directory_users = extract_users(elements)
    directory_lookup = {user['email']: user for user in directory_users}

    if not os.path.isfile("test.txt"):
        match_and_write_to_file(cloud_users, directory_lookup)


if __name__ == "__main__":
    elements = get_users(token, org_id)
    process_users(elements)

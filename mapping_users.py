import os
import requests
from dotenv import load_dotenv


load_dotenv()

token = os.getenv("TOKEN")
org_id = os.getenv("ORGID")


def get_users(token, org_id):
    headers = {"X-Cloud-Org-Id": f"{org_id}", "Authorization": f"OAuth {token}"}
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


def match_and_write_to_file(
                            cloud_users,
                            directory_users,
                            directory_lookup,
                            cloud_lookup,
                            filename="to.txt",
                            cloud_unique_users="unique_cloud_users.txt",
                            directory_unique_users="unique_directory_users.txt"
                            ):
    with (open(filename, "w") as file,
            open(cloud_unique_users, "w") as file_unique_cloud,
            open(directory_unique_users, "w") as file_unique_directory):
        for cloud_user in cloud_users:
            email = cloud_user['email']
            if email in directory_lookup:
                directory_user = directory_lookup[email]
                print(cloud_user['id'], directory_user['id'], directory_user['email'])
                #file.write(f"{directory_user['id']} {cloud_user['id']} #\n")    #для передачи задачи из 360 организации в облако
                file.write(f"{cloud_user['id']} {directory_user['id']} #\n")
            else:
                file_unique_cloud.write(f"{cloud_user['id']}\n")
        for directory_user in directory_users:
            if directory_user["email"] not in cloud_lookup:
                file_unique_directory.write(f"{directory_user["id"]}\n")


def process_users(elements):
    cloud_users, directory_users = extract_users(elements)
    directory_lookup = {user['email']: user for user in directory_users}
    cloud_lookup = {user['email']: user for user in cloud_users}

    if not os.path.isfile("to.txt"):
        match_and_write_to_file(cloud_users, directory_users, directory_lookup, cloud_lookup)


if __name__ == "__main__":
    elements = get_users(token, org_id)
    process_users(elements)

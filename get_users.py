import requests
from logger import logger
from settings import creds


def get_all_users() -> list:
    users = []
    page = 1
    per_page = 100

    while True:
        response = requests.get(
            f"{creds.baseurl}/users",
            headers=creds.headers,
            params={"page": page, "perPage": per_page},
        )
        response.raise_for_status()
        data = response.json()

        if not data:
            break

        users.extend(data)
        logger.info("Got page %d, users: %d", page, len(data))

        if len(data) < per_page:
            break

        page += 1

    logger.info("Users received: %d", len(users))
    return users


def save_users_to_file(users: list, filename: str = "users_info.txt") -> None:
    with open(filename, "w", encoding="utf-8") as file:
        for user in users:
            user_id = user.get("uid", "N/A")
            login = user.get("login", "N/A")
            email = user.get("email", "N/A")
            file.write(f"{user_id} {login} {email}\n")

    logger.info("Users information saved to file: %s", filename)


def main():
    try:
        users = get_all_users()
        if users:
            save_users_to_file(users)
            print(f"Info about {len(users)} users saved to file 'users_info.txt'")
        else:
            print("Didn't find any users")
    except requests.exceptions.RequestException as e:
        logger.error("Error while getting users: %s", e)
        raise


if __name__ == "__main__":
    main()

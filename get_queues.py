import requests
from logger import logger
from settings import creds


def get_all_queues() -> list:
    queues = []
    page = 1
    per_page = 100

    while True:
        response = requests.get(
            f"{creds.v3url}/queues",
            headers=creds.headers,
            params={"page": page, "perPage": per_page},
        )
        response.raise_for_status()
        data = response.json()

        if not data:
            break

        queues.extend(data)
        logger.info("Got page %d, queues: %d", page, len(data))

        if len(data) < per_page:
            break

        page += 1

    logger.info("Queues received: %d", len(queues))
    return queues


def save_queues_to_file(queues: list, filename: str = "queues.txt") -> None:
    with open(filename, "w", encoding="utf-8") as file:
        for q in queues:
            key = q.get("key", "N/A")
            file.write(f"{key}\n")
    logger.info("Users information saved to file: %s", filename)


def main():
    try:
        queues = get_all_queues()
        if queues:
            save_queues_to_file(queues)
            print(f"Info about {len(queues)} queues saved to file 'queues.txt'")
        else:
            print("Didn't find any queues")
    except requests.exceptions.RequestException as e:
        logger.error("Error while getting queues: %s", e)
        raise


if __name__ == "__main__":
    main()

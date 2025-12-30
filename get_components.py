import requests
from logger import logger


def get_all_components(creds) -> list:
    response = requests.get(
        f"{creds.baseurl}/components", headers=creds.headers
    )
    response.raise_for_status()
    elements = response.json()
    logger.info("%s", f"Server answered: {elements}\n")
    output_data = []
    for components in elements:
        output_data.append(components.get("id"))
    return output_data

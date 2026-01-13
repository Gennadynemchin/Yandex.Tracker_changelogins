import os
from dotenv import load_dotenv


load_dotenv()

ENTITY_TYPES = ["project", "portfolio", "goal"]

class Credentials:
    def __init__(self):
        self.baseurl = os.getenv("BASEURL")
        self.v3url = os.getenv("V3URL")
        self.orgid = os.getenv("ORGID")
        self.token = os.getenv("TOKEN")
        self.orgheader = os.getenv("ORGHEADER")
        self.queue = os.getenv("QUEUE")
        self.headers = {self.orgheader: self.orgid, "Authorization": f"OAuth {self.token}"}
        self.dryrun = os.getenv("DRY_RUN").lower() in ('true', '1', 'yes', 'on')


creds = Credentials()

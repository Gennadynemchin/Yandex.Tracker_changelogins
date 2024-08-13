import os
from dotenv import load_dotenv


load_dotenv()


class Credentials:
    def __init__(self):
        self.baseurl = os.getenv("BASEURL")
        self.orgid = os.getenv("ORGID")
        self.token = os.getenv("TOKEN")
        self.orgheader = os.getenv("ORGHEADER")


creds = Credentials()

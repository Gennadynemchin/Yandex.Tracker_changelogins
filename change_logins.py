import os
from yandex_tracker_client import TrackerClient
from dotenv import load_dotenv
from logger import logger


load_dotenv()

TOKEN = os.getenv("TOKEN")
ORG_ID = os.getenv("ORGID")
ORG_TYPE = os.getenv("ORGHEADER")


def changelogins(token, org_id, org_type):
    if org_type == "X-Cloud-Org-ID":
        client = TrackerClient(token=token, cloud_org_id=org_id)
    else:
        client = TrackerClient(token=token, org_id=org_id)
    per_page = 1000

    if os.path.isfile("to.txt"):
        text_file = open("to.txt", "r")
        data = text_file.readlines()
        text_file.close()
        for line in data:
            line = line.partition("\n")
            line = line[0]
            if (line.split(" " , 2)[1] != "") and (len(line.split(" " , 2)[1]) > 5):
                old_uid = line.split(" " , 2)[0]
                new_uid = line.split(" " , 2)[1]
                logger.info("Old: %s, New: %s", old_uid, new_uid)
                pages = 0
                current_page = 1
                logger.info("------Find issues with old Assignee------")
                while pages < current_page:
                    try:
                        issues = client.issues.find(filter={'assignee': old_uid}, per_page=per_page, page=current_page)

                        pages = issues.pages_count
                        for issue in issues:
                            try:
                                issue.update(assignee=new_uid)
                                logger.info("Assignee: %s", str(issue.key))
                            except Exception as e:
                                logger.error("Exception: %s", e)
                            if issue.createdBy.id == old_uid:
                                try:
                                    issue.update(author=new_uid)
                                    logger.info("CreatedBy update: %s", str(issue.key))
                                except Exception as e:
                                    logger.error("Exception: %s", e)
                    except Exception as e:
                        logger.error("Exception: %s", e)
                    pages = pages + 1
                logger.info("------Find issues with old CreatedBy-------")
                pages = 0
                current_page = 1
                while pages < current_page:
                    try:
                        issues = client.issues.find(filter={'createdBy': old_uid}, per_page=per_page, page=current_page)

                        pages = issues.pages_count
                        for issue in issues:
                            try:
                                issue.update(author=new_uid)
                                logger.info("CreatedBy update: %s", str(issue.key))
                            except Exception as e:
                                logger.error("Exception: %s", e)
                            if issue.assignee and (issue.assignee.id == old_uid):
                                try:
                                    issue.update(assignee=new_uid)
                                    logger.info("Assignee update: %s", str(issue.key))
                                except Exception as e:
                                    logger.error("Exception: %s", e)
                    except Exception as e:
                        logger.error("Exception: %s", e)
                    pages = pages + 1
                logger.info("------Find issues with old Followers-------")
                pages = 0
                current_page = 1
                while pages < current_page:
                    try:
                        issues = client.issues.find(filter={'followers': old_uid}, per_page=per_page, page=current_page)

                        pages = issues.pages_count
                        for issue in issues:
                            try:
                                logger.info(f"Followers update: {str(issue.key)}")
                                issue.update(followers={'add': new_uid})
                            except Exception as e:
                                logger.error("Exception: %s", e)
                            try:
                                logger.info(f"Followers update: {str(issue.key)}")
                                issue.update(followers={'remove': old_uid})
                            except Exception as e:
                                logger.error("Exception: %s", e)
                    except Exception as e:
                        logger.error("Exception: %s", e)
                    pages = pages + 1


if __name__ == "__main__":
    changelogins(TOKEN, ORG_ID, ORG_TYPE)

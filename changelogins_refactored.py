import os
from yandex_tracker_client import TrackerClient
from dotenv import load_dotenv


load_dotenv()

token = os.getenv("TOKEN")
org_id = os.getenv("ORGID")

per_page = 1000
client = TrackerClient(token=token, cloud_id=org_id)


if os.path.isfile("to.txt"): 
	text_file = open("to.txt", "r")
	data = text_file.readlines()
	text_file.close
	for line in data:
		line = line.partition("#")
		line = line[0]
		if (line.split(" " , 2)[1] != "") and (len(line.split(" " , 2)[1]) > 5):
			print(line.rstrip('\r\n'))
			old_uid = line.split(" " , 2)[0]
			new_uid = line.split(" " , 2)[1]
			print(f"Old: {old_uid}, New: {new_uid}")
			pages = 0
			current_page = 1
			print ("------Find issues with old Assignee------")
			while (pages < current_page):
				try:
					issues = client.issues.find(filter={'assignee': old_uid}, per_page=per_page, page=current_page)
					print(f"Total issues: {str(issues._items_count)}")
					print (f"Pages: {str(issues.pages_count)}")
					pages = issues.pages_count
				except Exception as e:
					print (e)

				for issue in issues:
					try:
						issue.update(assignee=new_uid)								
						print (f"Assignee update: {str(issue.key)}")
					except Exception as e:
						print (e)
					if issue.createdBy.id == old_uid:
						try:
							issue.update(author=new_uid)
							print (f"CreatedBy update: {str(issue.key)}")
						except Exception as e:
							print (e)
				pages = pages + 1
			print ("------Find issues with old CreatedBy-------")
			pages = 0
			current_page = 1
			while (pages < current_page):
				try:
					issues = client.issues.find(filter={'createdBy': old_uid}, per_page=per_page, page=current_page)
					print (f"Total issues: {str(issues._items_count)}")
					print (f"Pages: {str(issues.pages_count)}")
					pages = issues.pages_count
				except Exception as e:
					print (e)

				for issue in issues:
					try:
						issue.update(author=new_uid)
						print (f"CreatedBy update: {str(issue.key)}")
					except Exception as e:
						print (e)
					if (issue.assignee) and (issue.assignee.id == old_uid):
						try:
							issue.update(assignee=new_uid)
							print (f"Assignee update: {str(issue.key)}")
						except Exception as e:
							print (e)
				pages = pages + 1

			print ("------Find issues with old Followers-------")
			pages = 0
			current_page = 1
			while (pages < current_page):
				try:
					issues = client.issues.find(filter={'followers': old_uid}, per_page=per_page, page=current_page)
					print(f"Total issues: {str(issues._items_count)}")
					print(f"Pages: {str(issues.pages_count)}")
					pages = issues.pages_count
				except Exception as e:
					print(e)

				for issue in issues:
					try:
						print(f"Followers update:add: {str(issue.key)}")
						issue.update(followers={'add': new_uid})								
					except Exception as e:
						print(e)
					try:
						print(f"Followers update:remove: {str(issue.key)}")	
						issue.update(followers={'remove': old_uid})								
					except Exception as e:
						print(e)
				pages = pages + 1

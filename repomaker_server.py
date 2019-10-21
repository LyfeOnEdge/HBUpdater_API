import os, datetime

#--------------------------------------------------------------
JSON_RETRIES = 5
#--------------------------------------------------------------

if not os.path.isfile("log.txt"):
	with open("log.txt", "w+") as log:
		log.write("Made log at {}\n".format(datetime.date.today()))

def write_out(line):
	with open("log.txt", "a+") as log:
		log.write("{}\n".format(line))
	print(line)

try:
	import json, shutil, sys, requests
	from time import sleep
	import webhandler
	import repos
	from github import Github
	REPO_AUTHOR = "LyfeOnEdge"
	REPO_NAME = "HBUpdater_API"
	REPOFILENAME = "repos.json"
	OLDREPOFILENAME = "repos_old.json"
	OAUTHFILE = "oauth"
	SLEEP_INTERVAL = 30

	wd = os.path.dirname(os.path.abspath(__file__))

	new_repo = os.path.join(wd, REPOFILENAME)
	old_repo = os.path.join(wd, OLDREPOFILENAME)

	repourl = "https://api.github.com/repos/LyfeOnEdge/HBUpdater_API"
except Exception as e:
	write_out(e)

def make_repo():
	new_dict = {
		"homebrew" : repos.homebrewlist,
		"emulators" : repos.emulist,
		"games" : repos.gameslist,
		"media" : repos.medialist,
		"python" : repos.nxpythonlist,
		"cfw" : repos.customfirmwarelist,
		"payloads" : repos.payloadlist,
	}

	updated_packages = []
	for genre in new_dict.keys():
		for software_item in new_dict[genre]:
			updatefile = None
			attempt = 0
			while not updatefile and attempt < JSON_RETRIES:
				attempt += 1
				write_out("Downloading package {}, attempt {}".format(software_item["name"], attempt))
				updatefile, status = webhandler.getupdatedJson(software_item["name"], software_item["githubapi"])
			if not updatefile:
				write_out("ERROR BUILDING REPO FILE: Failed to get json for {}".format(software_item["name"]))
				return None, None
			if status:
				updated_packages.append(software_item["name"])
				
			with open(updatefile, encoding = "utf-8") as update_file_object:
				json_data = json.load(update_file_object)

			#Prune json
			for release in json_data:
				release.pop('assets_url', None)
				release.pop('name', None)
				release.pop('url', None)
				release.pop('target_commitish', None)
				release.pop('upload_url', None)
				release.pop('tarball_url', None)
				release.pop('html_url', None)
				release.pop('zipball_url', None)
				release.pop('node_id', None)
				release.pop('draft', None)
				release.pop('id', None)
				release.pop('prerelease', None)
				release.pop('author', None)
				assets = release["assets"]
				if assets:
					for asset in assets:
						asset.pop('uploader', None)
						asset.pop('node_id', None)
						asset.pop('id', None)
						asset.pop('url', None)
						asset.pop('created_at', None)
						asset.pop('label', None)
						asset.pop('state', None)

			software_item["github_content"] = json_data
			software_item["downloads"] = get_downloads(software_item, json_data)

	old_dict = None
	if os.path.isfile(new_repo):
		with open(new_repo) as old:
			old_dict = json.load(old)

	#if the repo has changed
	if new_dict == old_dict:
		return None, None
	else:
		#Make 1-instance backup for future checking
		if os.path.isfile(new_repo):
			shutil.move(new_repo, old_repo)

		#Print the new data
		print(json.dumps(new_dict, indent=4))

		with open(REPOFILENAME, 'w+') as outfile:
			json.dump(new_dict, outfile, indent=4)

		return REPOFILENAME, updated_packages

def get_downloads(software_item, json_data):
	ttl_dls = 0
	try:
		for release in json_data:
			asset = findassetchunk(software_item["pattern"], release["assets"])
			if asset:
				ttl_dls += asset["download_count"]
	except:
		write_out("Error getting downloads for {}".format(software_item["name"]))
	return ttl_dls

#matching the pattern or none found
def findassetchunk(pattern, assets):
	if not pattern:
		return

	if not assets:
		return

	for asset in assets:
		asseturl = asset["browser_download_url"]
		assetname = asseturl.rsplit("/",1)[1].lower()
		assetwithoutfiletype = assetname.split(".")[0]
		for firstpartpattern in pattern[0]:
			if firstpartpattern.lower() in assetwithoutfiletype.lower():
				if assetname.endswith(pattern[1].lower()):
					return asset


def create_release(g_obj, file, updated_pkgs):
	repo = g_obj.get_repo("{}/{}".format(REPO_AUTHOR,REPO_NAME))
	most_recent_release = repo.get_latest_release().tag_name
	most_recent_release = int(most_recent_release.strip("v"))
	tag = ("v{}".format(most_recent_release + 1))
	write_out(tag)
	t = datetime.datetime.time(datetime.datetime.now())
	timestamp = ("{} {}_{}_{}").format(datetime.date.today(), t.hour, t.minute, t.second) 
	write_out(timestamp)
	message = "this is repo version {}\nUpdated packages:\n{}".format(tag,json.dumps(updated_pkgs, indent = 4))

	release = repo.create_git_release(tag, timestamp, message, draft=False, prerelease=False, target_commitish="master")
	write_out("Release created sucessfully")
	release.upload_asset(file)
	write_out("uploaded repo file sucessfully")

try:
	webhandler.wait_for_connection()
	with open(OAUTHFILE) as f:
		oauth_token = f.read()
		g = Github(oauth_token)

	if oauth_token:
		webhandler.start(['Authorization', 'token %s' % oauth_token])
	else:
		sys.exit("No token")

	while True:
		write_out("Making repo at {}".format(datetime.datetime.now()))
		updated, updated_packages = make_repo()
		if updated:
			write_out("Data has changed.")
			write_out("Updated packages:\n{}".format(json.dumps(updated_packages, indent = 4)))
			create_release(g, updated, updated_packages)
		else:
			write_out("No data has changed.")
		write_out("Sleeping {} minutes".format(SLEEP_INTERVAL))
		sleep(60*SLEEP_INTERVAL)
except Exception as e:
	write_out(str(e))
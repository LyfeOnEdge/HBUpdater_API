import os, sys, shutil
from .etags import accessETaggedFile
from time import sleep
#web handling
import urllib.request 

#Variable to map previously downloaded jsons to minimize repeated downloads
filedict = {}

if not os.path.isdir("downloads"):
	os.mkdir("downloads")

def wait_for_connection():
	while True:
		try:
			downloadedfile, headers = urllib.request.urlretrieve("http://www.google.com")
			return
		except:
			print("waiting for internet connection...")
			sleep(1)
			pass

def start(header):
	opener = urllib.request.build_opener()
	opener.addheaders = [header, ('User-agent', 'Mozilla/5.0')]
	urllib.request.install_opener(opener)

#opens a url in a new tab
def opentab(url):
	import webbrowser
	webbrowser.open_new_tab(url)

#Download a file at a url, returns file path
def download(fileURL):
	try:
		downloadedfile, headers = urllib.request.urlretrieve(fileURL)
		print(headers)
		filename = headers["Content-Disposition"].split("filename=",1)[1]
		downloadlocation = os.path.join("downloads",filename)
		shutil.move(downloadedfile, downloadlocation)
		print("downloaded {} from url {}".format(filename, fileURL))
		return filename
	except Exception as e: 
		print(e)
		return None

def getJson(softwarename, apiurl):
	try:
		jsonfile = os.path.join("downloads", softwarename + ".json")
		jfile, status = accessETaggedFile(apiurl,jsonfile)
		return jfile
	except Exception as e:
		print("failed to download json file for {} - {}".format(softwarename, e))
		return None

def getupdatedJson(softwarename, apiurl):
	try:
		jsonfile = os.path.join("downloads", softwarename + ".json")
		jfile, status = accessETaggedFile(apiurl,jsonfile)
		return jfile, status
	except Exception as e:
		print("failed to download json file for {} - {}".format(softwarename, e))
		return None, None
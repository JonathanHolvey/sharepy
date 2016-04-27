import requests
import xml.etree.ElementTree as et
import re
import os
import pickle
from getpass import getpass
from datetime import datetime, timedelta
from copy import copy

def connect(site):
	return SharePointSession(site)

# load and return saved session object
def load(filename = None):
	filename = filename or "sp-session.pkl"
	if os.path.isfile(filename):
		session = pickle.load(open(filename, "rb"))
		if session.digest():
			print("Connected to " + session.site + " as " + session.username + "\n")
			return session
	else:
		return False

class SharePointSession:
	def __init__(self, site):
		self.site = site
		self.digestExpire = datetime.now()
		# request credentials from user
		self.username = input("Enter your username: ")

		if self.auth():
			self.digest()

			self.requiredHeaders = {
				"Cookie": self.cookie,
				"Accept": "application/json; odata=verbose",
				"Content-type": "application/json; odata=verbose"
			}

	def auth(self):
		# load SAML request template
		with open(os.path.join(os.path.dirname(__file__), "saml-template.xml"), "r") as file:
			samlRequest = file.read().replace(">\s+<", "><")

		# insert username and password into SAML request
		samlRequest = samlRequest.replace("[username]", self.username)
		samlRequest = samlRequest.replace("[password]", getpass("Enter your password: "))
		samlRequest = samlRequest.replace("[endpoint]", self.site)

		# request STS token from Microsoft Online
		print("Requesting STS token...")
		response = requests.post("https://login.microsoftonline.com/extSTS.srf", data = samlRequest)
		# parse and extract token from returned XML
		try:
			root = et.fromstring(response.text)
			token = root.find(".//{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd}BinarySecurityToken").text
		except:
			print("Token request failed. Check your username and password\n")
			return

		# request authorisation from sharepoint site
		print("Requesting authorisation cookies...")
		response = requests.post("https://" + self.site + "/_forms/default.aspx?wa=wsignin1.0", data = token, headers = {"Host": self.site})

		# create authorisation cookie from returned headers
		cookie = "rtFa=" + response.cookies["rtFa"] + "; FedAuth=" + response.cookies["FedAuth"]

		# verify authorisation by requesting page
		response = requests.get("https://" + self.site, headers = {"Cookie": cookie})

		if response.status_code == requests.codes.ok:
			self.cookie = cookie
			print("Authentication successful\n")
			return True
		else:
			print("Authentication failed\n")

	# check and refresh site's request form digest
	# see https://msdn.microsoft.com/en-us/library/office/jj164022.aspx#WritingData
	def digest(self):
		# check for expired digest
		if self.digestExpire <= datetime.now():
			# request site context info from SharePoint site
			response = requests.post("https://" + self.site + "/_api/contextinfo", data = "", headers = {"Cookie": self.cookie})
			# parse digest text and timeout from XML
			try:
				root = et.fromstring(response.text)
				self.digestText = root.find(".//{http://schemas.microsoft.com/ado/2007/08/dataservices}FormDigestValue").text
				digestTimeout = int(root.find(".//{http://schemas.microsoft.com/ado/2007/08/dataservices}FormDigestTimeoutSeconds").text)
			except:
				print("Digest request failed.\n")
				return
			# calculate digest expiry time
			self.digestExpire = datetime.now() + timedelta(seconds = digestTimeout)
			return True
		else:
			return True

	# serialise session object and save to file
	def save(self, filename = None):
		filename = filename or "sp-session.pkl"
		pickle.dump(self, open(filename, "wb"))

	def get(self, requestURI, headers = {}):
		allHeaders = copy(self.requiredHeaders)
		allHeaders.update(headers)
		return requests.get(requestURI, headers = allHeaders)

	def post(self, requestURI, data, headers = {}):
		self.digest()
		allHeaders = copy(self.requiredHeaders)
		allHeaders.update({"Authorization": "Bearer " + self.digestText})
		allHeaders.update(headers)
		return requests.post(requestURI, data = data, headers = allHeaders)

	def getfile(self, requestURI, filename = None, headers = {}):
		# extract file name from request URI
		if filename is None:
			filename = re.search("[^\/]+$", requestURI).group(0)
		# request file in stream mode
		allHeaders = copy(self.requiredHeaders)
		allHeaders.update(headers)
		response = requests.get(requestURI, headers = allHeaders, stream = True)
		# save to output file
		if response.status_code == requests.codes.ok:
			with open(filename, "wb") as file:
				for chunk in response:
					file.write(chunk)
			file.close()
		return response

import requests
import xml.etree.ElementTree as et
import re
import getpass

class Session:
	def __init__(self, site):
		self.site = site
		self.auth()

	def auth(self):
		# load SAML request template
		with open("saml-template.xml", "r") as file:
			samlRequest = file.read().replace(">\s+<", "><")

		# request credentials from user
		self.username = input("Enter your username: ")

		# insert username and password into SAML request
		samlRequest = samlRequest.replace("[username]", self.username)
		samlRequest = samlRequest.replace("[password]", getpass.getpass("Enter your password: "))
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
		response = requests.head("https://" + self.site, headers = {"Cookie": cookie})

		if response.status_code == requests.codes.ok or requests.codes.found:
			self.cookie = cookie
			self.expire = 0
			print("Authentication successful\n")
		else:
			self.expire = None
			print("Authentication failed\n")

	def get(self, requestURI):
		return requests.get(requestURI, headers = {"Cookie": self.cookie, "Accept": "application/json; odata=verbose"})

	def getfile(self, requestURI, filename = None):
		# extract file name from request URI
		if filename == None:
			filename = re.search("[^\/]+$", requestURI).group(0)
		# request file in stream mode
		response = requests.get(requestURI, headers = {"Cookie": self.cookie, "Accept": "application/json; odata=verbose"}, stream = True)
		# save to output file
		if response.status_code == requests.codes.ok:
			with open(filename, "wb") as file:
				for chunk in response:
					file.write(chunk)
			file.close()
		return response
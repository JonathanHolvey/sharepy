import requests
import xml.etree.ElementTree as et
import re
import getpass

class SPSession:
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
		response = requests.post("https://login.microsoftonline.com/extSTS.srf", data = samlRequest)
		# parse and extract token from returned XML
		root = et.fromstring(response.text)
		token = root.find(".//{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd}BinarySecurityToken").text

		# request authorisation from sharepoint site
		response = requests.post("https://" + self.site + "/_forms/default.aspx?wa=wsignin1.0", data = token, headers = {"Host": self.site})

		# parse authorisation cookies from returned headers
		cookies = []
		for item in response.headers["Set-Cookie"].split(", "):
			# trim data from end of cookie
			match = re.match("(.+?)(?=;)", item).group(1)
			# save two matching cookies to array
			if match[0:5] == "rtFa=" or match[0:8] == "FedAuth=":
				cookies.append(match)

		cookie = "; ".join(cookies)

		# verify authorisation by requesting page
		response = requests.get("https://" + self.site, headers = {"Cookie": cookie})
		
		if response.status_code == requests.codes.ok:
			self.cookie = cookie
			self.expire = 0
			print("Authentication successful")
		else:
			self.expire = None
			print("Authentication failed")

	def get(self, requestURI):
		return requests.get(requestURI, headers = {"Cookie": self.cookie, "Accept": "application/json; odata=verbose"})
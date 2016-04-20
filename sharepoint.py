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

		# parse authorisation cookies from returned headers
		cookies = []
		for item in response.headers["Set-Cookie"].split(", "):
			# trim data from end of cookie
			match = re.match("(.+?)(?=;)", item).group(1)
			# save two matching cookies to array
			if match[0:5] == "rtFa=" or match[0:8] == "FedAuth=":
				cookies.append(match)

		if len(cookies) != 2:
			print("Cookie request failed. Check your SharePoint site URL\n")

		cookie = "; ".join(cookies)

		# verify authorisation by requesting page
		response = requests.get("https://" + self.site, headers = {"Cookie": cookie})
		
		if response.status_code == requests.codes.ok:
			self.cookie = cookie
			self.expire = 0
			print("Authentication successful\n")
		else:
			self.expire = None
			print("Authentication failed\n")

	def get(self, requestURI):
		return requests.get(requestURI, headers = {"Cookie": self.cookie, "Accept": "application/json; odata=verbose"})
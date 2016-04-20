import requests
import xml.etree.ElementTree as et
import re

def spauth(endpoint, username, password):
	# load SAML request template
	with open("saml-template.xml", "r") as file:
		samlRequest = file.read().replace(">\s+<", "><")

	# insert username and password into SAML request
	samlRequest = samlRequest.replace("[username]", username)
	samlRequest = samlRequest.replace("[password]", password)
	samlRequest = samlRequest.replace("[endpoint]", endpoint)

	# request STS token from Microsoft Online
	response = requests.post("https://login.microsoftonline.com/extSTS.srf", data = samlRequest)
	# parse and extract token from returned XML
	root = et.fromstring(response.text)
	token = root.find(".//{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd}BinarySecurityToken").text

	# request authorisation from sharepoint site
	response = requests.post("https://" + endpoint + "/_forms/default.aspx?wa=wsignin1.0", data = token, headers = {"Host": endpoint})

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
	response = requests.get("https://" + endpoint, headers = {"Cookie": cookie})
	
	if response.status_code == requests.codes.ok:
		return cookie
	else:
		response.raise_for_status()
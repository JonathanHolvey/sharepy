import os
import xml.etree.ElementTree as et
from getpass import getpass
from datetime import datetime, timedelta
from xml.sax.saxutils import escape

import requests


# XML namespace URLs
ns = {
    "wsse": "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd",
    "psf": "http://schemas.microsoft.com/Passport/SoapServices/SOAPFault",
    "d": "http://schemas.microsoft.com/ado/2007/08/dataservices",
    "S": "http://www.w3.org/2003/05/soap-envelope"
}


def detect(username, password=None):
    """Detect authentication type and URL"""
    realm_url = "https://login.microsoftonline.com/GetUserRealm.srf?login={}&xml=1"
    root = et.fromstring(requests.get(realm_url.format(escape(username))).text)
    auth_type = root.find("NameSpaceType").text.lower()
    # For regular SharePoint Online authentication
    if auth_type != "federated":
        auth_domain = root.find("CloudInstanceName").text
        auth_url = "https://login.{}/extSTS.srf".format(auth_domain)
        return SharePointOnline(username=username, password=password, auth_url=auth_url)
    # For federated ADFS authentication
    else:
        auth_url = root.find("STSAuthUrl").text
        return


class SharePointOnline():
    """A Requests authentication class for SharePoint Online"""
    def __init__(self, username, password=None, auth_url=None):
        self.site = None
        self.username = username
        self.password = password
        self.auth_url = auth_url or "https://login.microsoftonline.com/extSTS.srf"
        self.expire = datetime.now()
        self.cookie = None
        self.digest = None

    def __call__(self, request):
        """Inject cookies into requests as they are made"""
        if self.cookie and self.digest:
            request.headers.update({"Cookie": self.cookie,
                                    "Authorization": "Bearer " + self.digest})
        return request

    def get_token(self):
        """Request authentication token from Microsoft"""
        # Load SAML request template
        with open(os.path.join(os.path.dirname(__file__), "saml-template.xml"), "r") as file:
            saml = file.read()

        # Insert username and password into SAML request after escaping special characters
        password = self.password or getpass("Enter your password: ")
        saml = saml.format(username=escape(self.username),
                           password=escape(password),
                           site=self.site)

        # Request security token from Microsoft Online
        print("Requesting security token...\r", end="")
        try:
            response = requests.post(self.auth_url, data=saml)
        except requests.exceptions.ConnectionError:
            print("Could not connect to", self.auth_url)
            return
        # Parse and extract token from returned XML
        try:
            root = et.fromstring(response.text)
        except et.ParseError:
            print("Token request failed. The server did not send a valid response")
            return

        # Extract token from returned XML
        token = root.find(".//wsse:BinarySecurityToken", ns)
        # Check for errors and print error messages
        if token is None or root.find(".//S:Fault", ns) is not None:
            print("{}: {}".format(root.find(".//S:Text", ns).text,
                                  root.find(".//psf:text", ns).text).strip().strip("."))
            return
        return token.text

    def get_cookie(self, token):
        """Request access cookie from sharepoint site"""
        print("Requesting access cookie... \r", end="")
        response = requests.post("https://" + self.site + "/_forms/default.aspx?wa=wsignin1.0",
                                 data=token, headers={"Host": self.site})

        # Create access cookie from returned headers
        cookie = self._buildcookie(response.cookies)
        # Verify access by requesting page
        response = requests.get("https://" + self.site + "/_api/web", headers={"Cookie": cookie})

        if response.status_code == requests.codes.ok:
            print("Authentication successful   ")
            self.cookie = cookie
            return True
        else:
            print("Authentication failed       ")

    def get_digest(self):
        """Check and refresh sites cookie and request digest"""
        if self.expire <= datetime.now():
            # Request site context info from SharePoint site
            response = requests.post("https://" + self.site + "/_api/contextinfo",
                                     data="", headers={"Cookie": self.cookie})
            # Parse digest text and timeout from XML
            try:
                root = et.fromstring(response.text)
                self.digest = root.find(".//d:FormDigestValue", ns).text
                self.cookie = self._buildcookie(response.cookies)
                timeout = int(root.find(".//d:FormDigestTimeoutSeconds", ns).text)
            except:
                print("Digest request failed")
                return
            # Calculate digest expiry time
            self.expire = datetime.now() + timedelta(seconds=timeout)

        return True

    def login(self, site):
        """Perform authentication steps. Return True on success"""
        self.site = site
        token = self.get_token()
        if token and self.get_cookie(token):
            self.get_digest()

    def _buildcookie(self, cookies):
        """Create session cookie from response cookie dictionary"""
        return "rtFa=" + cookies["rtFa"] + "; FedAuth=" + cookies["FedAuth"]

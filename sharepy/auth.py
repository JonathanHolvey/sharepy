import os
import xml.etree.ElementTree as et
from getpass import getpass
from datetime import datetime, timedelta
from xml.sax.saxutils import escape
from uuid import uuid4
import re

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
    auth_type = root.find("NameSpaceType").text
    # For regular SharePoint Online authentication
    if auth_type == "Managed":
        auth_domain = root.find("CloudInstanceName").text
        auth_url = "https://login.{}/extSTS.srf".format(auth_domain)
        return SharePointOnline(username=username, password=password, auth_url=auth_url)
    # For federated ADFS authentication
    elif auth_type == "Federated":
        auth_url = root.find("STSAuthURL").text
        return SharePointADFS(username=username, password=password, auth_url=auth_url)
    else:
        print("'{}' namespace sites are not supported").format(auth_type)
        return None


class SharePointOnline(requests.auth.AuthBase):
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
        self._get_digest()
        if self.cookie and self.digest:
            request.headers.update({"Cookie": self.cookie,
                                    "Authorization": "Bearer " + self.digest})
        return request

    def login(self, site):
        """Perform authentication steps"""
        self.site = site
        token = self._get_token()
        if token and self._get_cookie(token):
            self._get_digest()

    def _get_token(self):
        """Request authentication token from Microsoft"""
        # Load SAML request template
        with open(os.path.join(os.path.dirname(__file__),
                               "saml-templates/sp-online.xml"), "r") as file:
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

    def _get_cookie(self, token):
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

    def _get_digest(self):
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

    def _buildcookie(self, cookies):
        """Create session cookie from response cookie dictionary"""
        return "rtFa=" + cookies["rtFa"] + "; FedAuth=" + cookies["FedAuth"]


class SharePointADFS(requests.auth.AuthBase):
    """A Requests authentication class for SharePoint sites with federated authentication
    Ported from https://github.com/Zerg00s/XSOM/blob/master/XSOM/Authenticator.cs"""
    def __init__(self, username, password=None, auth_url=None):
        self.username = username
        self.password = password
        self.auth_url = auth_url
        self.token = None
        self.cookie = None
        self.expire = datetime.now()
        self.tenantBaseURL = None
        self.digest = None

    def __call__(self, request):
        """Inject cookies into requests as they are made"""
        if self.cookie and self.digest:
            request.headers.update({"Content-Type": "text/xml; charset=utf-8",
                                    "Cookie" : self.cookie})
        return request

    def login(self, site):
        """Perform authentication steps"""
        self.site = site
        # check if http(s) is prepended (not found < 0)
        if site.find('://') < 0:
            self.tenantBaseURL = re.search(r"([^/]+)", site).group(0)
        else: # http(s) exists
            self.tenantBaseURL = re.serach(r'/{2}([^/]+)', site).group(1)
        self.tenantBaseURL.find
        self._get_token()
        self._get_cookie()
        self._get_digest()

    def _get_token(self):
        """Request authentication token from ADFS server"""
        # Generate timestamps and GUID
        created = datetime.utcnow()
        createdStr = str(datetime.utcnow()).replace(' ', 'T') + 'Z'
        expires = created + timedelta(minutes=10)
        expiresStr = str(expires).replace(' ', 'T') + 'Z'
        message_id = str(uuid4())

        # Load SAML request template
        with open(os.path.join(os.path.dirname(__file__),
                               "saml-templates/sp-adfs-stsAuthAssertion.xml"), "r") as file:
            saml = file.read()
        
        # Define headers to request the token
        headers = {"Content-Type": "application/soap+xml; charset=utf-8"}

        # Insert variables into SAML request
        password = self.password or getpass("Enter your password: ")
        saml = saml.format(username=escape(self.username),
                           password=escape(password),
                           auth_url=self.auth_url,
                           message_id=message_id,
                           created=createdStr,
                           expires=expiresStr)
        
        # Request security token from Microsoft Online
        print("Requesting security token...\r", end="")
        try:
            response = requests.post(self.auth_url, data=saml, headers=headers)
        except requests.exceptions.ConnectionError:
            print("Could not connect to", self.auth_url)
            return
        # Parse and extract token from returned XML
        try:
            root = et.fromstring(response.text)
        except et.ParseError:
            print("Token request failed. The server did not send a valid response\r", end="")
            return
        try:
            samlAssertion = (re.search(r'<saml:Assertion.*\/saml:Assertion>', response.text)).group(0)
        except AttributeError:
            print("Token requested, but response did not include the STS SAML Assertion.\r", end="")
            return
        
        print("SAML Assertion received.")

        # Get the BinarySecurityToken

        # Define MS Online authentication REST endpoint
        MSO_AUTH_URL = "https://login.microsoftonline.com/rst2.srf"

        with open(os.path.join(os.path.dirname(__file__), 
                "saml-templates/sp-adfs-stsBinaryToken.xml"), "r") as file:
            saml = file.read()

        # Format saml to receive BinarySecurityToken
        saml = saml.format(customSTSAssertion=samlAssertion,
                           msoEndpoint="sharepoint.com")
        response = requests.post(url=MSO_AUTH_URL, data=saml, headers=headers)
        # Parse and extract token from returned XML
        try:
            root = et.fromstring(response.text)
        except et.ParseError:
            print("BinarySecurityToken request failed. The server did not send a valid response\r", end="")
            return
        try:
            binarySecurityToken = (re.search(r'BinarySecurityToken Id.*>([^<]+)', response.text)).group(1)
        except AttributeError:
            print("BinarySecurityToken requested, but response did not include the STS SAML Assertion.\r", end="")
            return
        
        print("BinarySecurityToken received.")
        self.token = binarySecurityToken

        return True
    
    def _get_cookie(self):
        # regex will get the 'tenant url' from the site provided for login
        #SPO_IDCRL_URL = "https://" + re.search('(.+\.com)/', self.site).group(1) + "/_vti_bin/idcrl.svc/"
        SPO_IDCRL_URL = "https://" + self.tenantBaseURL + "/_vti_bin/idcrl.svc/"
        # HTTP Post request with authorization headers
        headers = {"Authorization": "BPOSIDCRL " + self.token, 
                   "X-IDCRL_ACCEPTED":"t", 
                   "User-Agent": "" }
        response = requests.get(url=SPO_IDCRL_URL, headers=headers)

        if response.status_code == requests.codes.ok:
            print("ADFS Authentication successful")

            # Add the SPOIDCRL cookie to the session
            self.cookie = self._buildcookie(response.cookies)
            
            return True
        else:
            print("ADFS Authentication failed")

    def _get_digest(self):
        """Check and refresh sites cookie and request digest"""
        
        if self.expire <= datetime.now():
            # Template for SOAP digest request using <tenant>.sharepoint.com/sites/<sub site>/_vti_bin/sites
            headers = ({"SOAPAction": "http://schemas.microsoft.com/sharepoint/soap/GetUpdatedFormDigestInformation",
                                "Host" : self.tenantBaseURL,
                                "Content-Type" : "text/xml;charset=utf-8",
                                "Cookie" : self.cookie,
                                "X-RequestForceAuthentication" : "true"})
            
            with open(os.path.join(os.path.dirname(__file__), 
                    "saml-templates/sp-updateDigest.xml"), "r") as file:
                    digestEnvelope = file.read()

            # Request site context info from SharePoint site
            requestUrl = "https://" + self.tenantBaseURL + "/_vti_bin/sites.asmx"
            response = requests.post(requestUrl, data=digestEnvelope, headers=headers)
            
            # Parse digest text and timeout from XML
            try:   
                self.digest = re.search(r"<DigestValue>(.+)</DigestValue>", response.text).group(1)
                timeout = int(re.search(r"Seconds>(\d+)<", response.text).group(1))  
            except:
                print("Digest request failed")
                return

            # Calculate digest expiry time
            self.expire = datetime.now() + timedelta(seconds=timeout)

        return True
    def _buildcookie(self, cookies):
        """Create session cookie from response cookie dictionary"""
        
        return "SPOIDCRL=" + cookies["SPOIDCRL"]

import os
import re
import requests
import xml.etree.ElementTree as et
import pickle
from getpass import getpass
from datetime import datetime, timedelta

# XML namespace URLs
ns = {
    "wsse": "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd",
    "d": "http://schemas.microsoft.com/ado/2007/08/dataservices"
}


def connect(site):
    return SharePointSession(site)


def load(filename="sp-session.pkl"):
    """Load and return saved session object"""
    session = SharePointSession()
    session.__dict__.update(pickle.load(open(filename, "rb")))
    if session._redigest() or session._spauth():
        print("Connected to {} as {}\n".format(session.site, session.username))
        # Re-save session to prevent it going stale
        try:
            session.save(filename)
        except:
            pass
        return session


class SharePointSession(requests.Session):
    """A SharePy Requests session.

    Provide session authentication to SharePoint Online sites
    in addition to standard functionality provided by Requests.

    Basic Usage::
      >>> import sharepy
      >>> s = sharepy.connect("example.sharepoint.com")
      >>> s.get("https://exemple.sharepoint.com/_api/web/lists")
      <Response [200]>
    """

    def __init__(self, site=None):
        super().__init__()
        self.password = None

        if site is not None:
            self.site = re.sub(r"^https?://", "", site)
            self.expire = datetime.now()
            # Request credentials from user
            self.username = input("Enter your username: ")

            if self._spauth():
                self._redigest()
                self.headers.update({
                    "Accept": "application/json; odata=verbose",
                    "Content-type": "application/json; odata=verbose"
                })

    def _spauth(self):
        """Authorise SharePoint session by generating session cookie"""
        # Load SAML request template
        with open(os.path.join(os.path.dirname(__file__), "saml-template.xml"), "r") as file:
            saml = file.read()

        # Insert username and password into SAML request
        password = self.password or getpass("Enter your password: ")
        saml = saml.format(username=self.username,
                           password=password,
                           site=self.site)

        # Request security token from Microsoft Online
        print("Requesting security token...")
        response = requests.post("https://login.microsoftonline.com/extSTS.srf", data=saml)
        # Parse and extract token from returned XML
        try:
            root = et.fromstring(response.text)
            token = root.find(".//wsse:BinarySecurityToken", ns).text
        except:
            print("Token request failed. Check your username and password\n")
            return

        # Request access token from sharepoint site
        print("Requesting access cookie...")
        response = requests.post("https://" + self.site + "/_forms/default.aspx?wa=wsignin1.0",
                                 data=token, headers={"Host": self.site})

        # Create access cookie from returned headers
        cookie = self._buildcookie(response.cookies)
        # Verify access by requesting page
        response = requests.get("https://" + self.site + "/_api/web", headers={"Cookie": cookie})

        if response.status_code == requests.codes.ok:
            self.headers.update({"Cookie": cookie})
            self.cookie = cookie
            print("Authentication successful\n")
            return True
        else:
            print("Authentication failed\n")

    def _redigest(self):
        """Check and refresh site's request form digest"""
        if self.expire <= datetime.now():
            # Request site context info from SharePoint site
            response = requests.post("https://" + self.site + "/_api/contextinfo",
                                     data="", headers={"Cookie": self.cookie})
            # Parse digest text and timeout from XML
            try:
                root = et.fromstring(response.text)
                self.digest = root.find(".//d:FormDigestValue", ns).text
                timeout = int(root.find(".//d:FormDigestTimeoutSeconds", ns).text)
                self.headers.update({"Cookie": self._buildcookie(response.cookies)})
            except:
                print("Digest request failed")
                return
            # Calculate digest expiry time
            self.expire = datetime.now() + timedelta(seconds=timeout)

        return self.digest

    def save(self, filename="sp-session.pkl"):
        """Serialise session object and save to file"""
        mode = "r+b" if os.path.isfile(filename) else "wb"
        pickle.dump(self.__dict__, open(filename, mode))

    def post(self, url, *args, **kwargs):
        """Make POST request and include authorisation headers"""
        if "headers" not in kwargs.keys():
            kwargs["headers"] = {}
        kwargs["headers"]["Authorization"] = "Bearer " + self._redigest()

        return super().post(url, *args, **kwargs)

    def getfile(self, url, *args, **kwargs):
        """Stream download of specified URL and output to file"""
        # Extract file name from request URL if not provided as keyword argument
        filename = kwargs.pop("filename", re.search("[^\/]+$", url).group(0))
        kwargs["stream"] = True
        # Request file in stream mode
        response = self.get(url, *args, **kwargs)
        # Save to output file
        if response.status_code == requests.codes.ok:
            with open(filename, "wb") as file:
                for chunk in response:
                    file.write(chunk)
        return response

    def _buildcookie(self, cookies):
        """Create session cookie from response cookie dictionary"""
        return "rtFa=" + cookies["rtFa"] + "; FedAuth=" + cookies["FedAuth"]

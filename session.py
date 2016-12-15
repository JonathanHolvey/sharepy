import os
import re
import requests
import xml.etree.ElementTree as et
import pickle
from getpass import getpass
from datetime import datetime, timedelta

# XML namespace URLs
xmlns = {
    "wsse": "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd",
    "d": "http://schemas.microsoft.com/ado/2007/08/dataservices"
}


def connect(site):
    return SharePointSession(site)


# Load and return saved session object
def load(filename="sp-session.pkl"):
    session = SharePointSession()
    session.__dict__.update(pickle.load(open(filename, "rb")))
    if session.redigest(force=True) or session.spauth():
        print("Connected to {} as {}\n".format(session.site, session.username))
        # Re-save session to prevent it going stale
        try:
            session.save(filename)
        except:
            pass
        return session


class SharePointSession(requests.Session):
    def __init__(self, site=None):
        super().__init__()
        self.password = None

        if site is not None:
            self.site = re.sub(r"^https?://", "", site)
            self.expire = datetime.now()
            # Request credentials from user
            self.username = input("Enter your username: ")

            if self.spauth():
                self.redigest()
                self.headers.update({
                    "Accept": "application/json; odata=verbose",
                    "Content-type": "application/json; odata=verbose"
                })

    def spauth(self):
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
            token = root.find(".//{" + xmlns["wsse"] + "}BinarySecurityToken").text
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

    # Check and refresh site's request form digest
    def redigest(self, force=False):
        # Check for expired digest
        if self.expire <= datetime.now() or force:
            # Request site context info from SharePoint site
            response = requests.post("https://" + self.site + "/_api/contextinfo",
                                     data="", headers={"Cookie": self.cookie})
            # Parse digest text and timeout from XML
            try:
                root = et.fromstring(response.text)
                self.digest = root.find(".//{" + xmlns["d"] + "}FormDigestValue").text
                timeout = int(root.find(".//{" + xmlns["d"] + "}FormDigestTimeoutSeconds").text)
                self.headers.update({"Cookie": self._buildcookie(response.cookies)})
            except:
                print("Digest request failed")
                return
            # Calculate digest expiry time
            self.expire = datetime.now() + timedelta(seconds=timeout)

        return self.digest

    # Serialise session object and save to file
    def save(self, filename="sp-session.pkl"):
        mode = "r+b" if os.path.isfile(filename) else "wb"
        pickle.dump(self.__dict__, open(filename, mode))

    def post(self, url, *args, **kwargs):
        if "headers" not in kwargs.keys():
            kwargs["headers"] = {}
        kwargs["headers"]["Authorization"] = "Bearer " + self.redigest()

        return super().post(url, *args, **kwargs)

    def getfile(self, url, *args, **kwargs):
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
            file.close()
        return response

    # Create session cookie from response cookie dictionary
    def _buildcookie(self, cookies):
        return "rtFa=" + cookies["rtFa"] + "; FedAuth=" + cookies["FedAuth"]

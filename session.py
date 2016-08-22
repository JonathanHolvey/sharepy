import os
import re
import requests
import xml.etree.ElementTree as et
import pickle
from getpass import getpass
from datetime import datetime, timedelta

def connect(site):
    return SharePointSession(site)

# Load and return saved session object
def load(filename="sp-session.pkl"):
    session = SharePointSession()
    session.__dict__ = pickle.load(open(filename, "rb"))
    if session.redigest(True):
        print("Connected to " + session.site + " as " + session.username + "\n")
        return session
    else:
        return False

class SharePointSession(requests.Session):
    def __init__(self, site=None):
        super().__init__()

        if site is not None:
            self.site = site
            self.expire = datetime.now()
            # Request credentials from user
            self.username = input("Enter your username: ")

            if self.spauth():
                self.redigest()

                self.headers.update({
                    "Cookie": self.cookie,
                    "Accept": "application/json; odata=verbose",
                    "Content-type": "application/json; odata=verbose"
                })

    def spauth(self):
        # Load SAML request template
        with open(os.path.join(os.path.dirname(__file__), "saml-template.xml"), "r") as file:
            saml = file.read().replace(">\s+<", "><")

        # Insert username and password into SAML request
        saml = saml.format(username=self.username, password=getpass("Enter your password: "), site=self.site)

        # Request STS token from Microsoft Online
        print("Requesting STS token...")
        response = requests.post("https://login.microsoftonline.com/extSTS.srf", data=saml)
        # Parse and extract token from returned XML
        try:
            root = et.fromstring(response.text)
            token = root.find(".//{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd}BinarySecurityToken").text
        except:
            print("Token request failed. Check your username and password\n")
            return

        # Request authorisation from sharepoint site
        print("Requesting authorisation cookies...")
        response = requests.post("https://" + self.site + "/_forms/default.aspx?wa=wsignin1.0", data=token, headers={"Host": self.site})

        # Create authorisation cookie from returned headers
        cookie = "rtFa=" + response.cookies["rtFa"] + "; FedAuth=" + response.cookies["FedAuth"]

        # Verify authorisation by requesting page
        response = requests.get("https://" + self.site, headers={"Cookie": cookie})

        if response.status_code == requests.codes.ok:
            self.cookie = cookie
            print("Authentication successful\n")
            return True
        else:
            print("Authentication failed\n")

    # Check and refresh site's request form digest
    # See https://msdn.microsoft.com/en-us/library/office/jj164022.aspx#WritingData
    def redigest(self, force=False):
        # Check for expired digest
        if self.expire <= datetime.now() or force:
            # Request site context info from SharePoint site
            response = requests.post("https://" + self.site + "/_api/contextinfo", data="", headers={"Cookie": self.cookie})
            # Parse digest text and timeout from XML
            try:
                root = et.fromstring(response.text)
                self.digest = root.find(".//{http://schemas.microsoft.com/ado/2007/08/dataservices}FormDigestValue").text
                timeout = int(root.find(".//{http://schemas.microsoft.com/ado/2007/08/dataservices}FormDigestTimeoutSeconds").text)
            except:
                print("Digest request failed.\n")
                return
            # Calculate digest expiry time
            self.expire = datetime.now() + timedelta(seconds=timeout)

        return self.digest

    # Serialise session object and save to file
    def save(self, filename="sp-session.pkl"):
        pickle.dump(self.__dict__, open(filename, "wb"))

    def post(self, url, *args, **kwargs):
        if "headers" not in kwargs.keys():
            kwargs["headers"] = {}
        kwargs["headers"]["Authorization"] = "Bearer " + self.redigest()

        return super().post(url, *args, **kwargs)

    def getfile(self, url, *args, **kwargs):
        # Extract file name from request URL
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

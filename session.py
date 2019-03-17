from __future__ import with_statement
from __future__ import absolute_import
import os
import re
import requests
import xml.etree.ElementTree as et
import pickle
from getpass import getpass
from datetime import datetime, timedelta
from xml.sax.saxutils import escape
from io import open
import sys

# XML namespace URLs
ns = {
    u"wsse": u"http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd",
    u"d": u"http://schemas.microsoft.com/ado/2007/08/dataservices"
}


def connect(site, username=None, password=None):
    return SharePointSession(site, username, password)


def load(filename=u"sp-session.pkl"):
    u"""Load and return saved session object"""
    session = SharePointSession()
    session.__dict__.update(pickle.load(open(filename, u"rb")))
    if session._redigest() or session._spauth():
        print u"Connected to {} as {}".format(session.site, session.username)
        # Re-save session to prevent it going stale
        try:
            session.save(filename)
        except:
            pass
        return session


class SharePointSession(requests.Session):
    u"""A SharePy Requests session.

    Provide session authentication to SharePoint Online sites
    in addition to standard functionality provided by Requests.

    Basic Usage::
      >>> import sharepy
      >>> s = sharepy.connect("example.sharepoint.com")
      >>> s.get("https://exemple.sharepoint.com/_api/web/lists")
      <Response [200]>
    """

    def __init__(self, site=None, username=None, password=None):
        super(SharePointSession, self).__init__()

        if site is not None:
            self.site = re.sub(ur"^https?://", u"", site)
            self.expire = datetime.now()
            # Request credentials from user
            self.username = username or raw_input(u"Enter your username: ")
            self.password = password

            if self._spauth():
                self._redigest()
                self.headers.update({
                    u"Accept": u"application/json; odata=verbose",
                    u"Content-type": u"application/json; odata=verbose"
                })

    def _spauth(self):
        u"""Authorise SharePoint session by generating session cookie"""
        # Load SAML request template
        with open(os.path.join(os.path.dirname(__file__), u"saml-template.xml"), u"r") as file:
            saml = file.read()

        # Insert username and password into SAML request after escaping special characters
        password = self.password or getpass(u"Enter your password: ")
        saml = saml.format(username=escape(self.username),
                           password=escape(password),
                           site=self.site)

        # Request security token from Microsoft Online
        print u"Requesting security token...\r",; sys.stdout.write(u"")
        response = requests.post(u"https://login.microsoftonline.com/extSTS.srf", data=saml)
        # Parse and extract token from returned XML
        try:
            root = et.fromstring(response.text)
            token = root.find(u".//wsse:BinarySecurityToken", ns).text
        except:
            print u"Token request failed. Check your username and password"
            return

        # Request access token from sharepoint site
        print u"Requesting access cookie... \r",; sys.stdout.write(u"")
        response = requests.post(u"https://" + self.site + u"/_forms/default.aspx?wa=wsignin1.0",
                                 data=token, headers={u"Host": self.site})

        # Create access cookie from returned headers
        cookie = self._buildcookie(response.cookies)
        # Verify access by requesting page
        response = requests.get(u"https://" + self.site + u"/_api/web", headers={u"Cookie": cookie})

        if response.status_code == requests.codes.ok:
            self.headers.update({u"Cookie": cookie})
            self.cookie = cookie
            print u"Authentication successful   "
            return True
        else:
            print u"Authentication failed       "

    def _redigest(self):
        u"""Check and refresh site's request form digest"""
        if self.expire <= datetime.now():
            # Request site context info from SharePoint site
            response = requests.post(u"https://" + self.site + u"/_api/contextinfo",
                                     data=u"", headers={u"Cookie": self.cookie})
            # Parse digest text and timeout from XML
            try:
                root = et.fromstring(response.text)
                self.digest = root.find(u".//d:FormDigestValue", ns).text
                timeout = int(root.find(u".//d:FormDigestTimeoutSeconds", ns).text)
                self.headers.update({u"Cookie": self._buildcookie(response.cookies)})
            except:
                print u"Digest request failed"
                return
            # Calculate digest expiry time
            self.expire = datetime.now() + timedelta(seconds=timeout)

        return self.digest

    def save(self, filename=u"sp-session.pkl"):
        u"""Serialise session object and save to file"""
        mode = u"r+b" if os.path.isfile(filename) else u"wb"
        pickle.dump(self.__dict__, open(filename, mode))

    def post(self, url, *args, **kwargs):
        u"""Make POST request and include authorisation headers"""
        if u"headers" not in kwargs.keys():
            kwargs[u"headers"] = {}
        kwargs[u"headers"][u"Authorization"] = u"Bearer " + self._redigest()

        return super(SharePointSession, self).post(url, *args, **kwargs)

    def getfile(self, url, *args, **kwargs):
        u"""Stream download of specified URL and output to file"""
        # Extract file name from request URL if not provided as keyword argument
        filename = kwargs.pop(u"filename", re.search(u"[^\/]+$", url).group(0))
        kwargs[u"stream"] = True
        # Request file in stream mode
        response = self.get(url, *args, **kwargs)
        # Save to output file
        if response.status_code == requests.codes.ok:
            with open(filename, u"wb") as file:
                for chunk in response:
                    file.write(chunk)
        return response

    def _buildcookie(self, cookies):
        u"""Create session cookie from response cookie dictionary"""
        return u"rtFa=" + cookies[u"rtFa"] + u"; FedAuth=" + cookies[u"FedAuth"]

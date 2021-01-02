from getpass import getpass
from datetime import datetime, timedelta
from xml.sax.saxutils import escape
import xml.etree.ElementTree as et

import requests

from .base import BaseAuth
from .xml import namespaces as ns
from . import templates
from .. import errors


class SharePointOnline(BaseAuth):
    """Authenticate via SharePoint Online"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.expire = datetime.now()
        self.token = None

    def login(self, site):
        """Perform authentication steps"""
        self.site = site
        self._get_token()
        self._get_cookie()
        self._get_digest()

    def refresh(self):
        return self._get_digest()

    def _get_token(self):
        # Insert username and password into SAML request after escaping special characters
        password = self.password or getpass('Enter your password: ')
        saml = templates.load('spol-token.saml').format(username=escape(self.username),
                                                        password=escape(password),
                                                        site=self.site)

        # Request security token from Microsoft Online
        response = requests.post(self.login_url, data=saml)
        # Parse and extract token from returned XML
        try:
            root = et.fromstring(response.text)
        except et.ParseError:
            raise errors.AuthError('Token request failed. Invalid server response')

        # Extract token from returned XML
        token = root.find('.//wsse:BinarySecurityToken', ns)
        # Check for errors and print error messages
        if token is None or root.find('.//S:Fault', ns) is not None:
            print(response.text)
            raise errors.AuthError.fromxml(root)

        self.token = token.text

    def _get_cookie(self):
        """Request access cookie from sharepoint site"""
        cookie_url = f'https://{self.site}/_forms/default.aspx?wa=wsignin1.0'
        response = requests.post(cookie_url, data=self.token, headers={'Host': self.site})

        # Create access cookie from returned headers
        cookie = self._buildcookie(response.cookies)
        # Verify access by requesting page
        test_url = f'https://{self.site}/_api/web'
        response = requests.get(test_url, headers={'Cookie': cookie})

        if response.status_code == requests.codes.ok:
            self.cookie = cookie
        else:
            raise errors.AuthError('Authentication failed')

    def _get_digest(self):
        """Check and refresh sites cookie and request digest"""
        if self.expire <= datetime.now():
            # Request site context info from SharePoint site
            digest_url = f'https://{self.site}/_api/contextinfo'
            response = requests.post(digest_url, data='', headers={'Cookie': self.cookie})
            # Parse digest text and timeout from XML
            try:
                root = et.fromstring(response.text)
                self.digest = root.find('.//d:FormDigestValue', ns).text
                self.cookie = self._buildcookie(response.cookies)
                timeout = int(root.find('.//d:FormDigestTimeoutSeconds', ns).text)
            except Exception:
                raise errors.AuthError('Digest request failed')
            # Calculate digest expiry time
            self.expire = datetime.now() + timedelta(seconds=timeout)

        return True

    def _buildcookie(self, cookies):
        """Create session cookie from response cookie dictionary"""
        return 'rtFa=' + cookies['rtFa'] + '; FedAuth=' + cookies['FedAuth']

    @staticmethod
    def supports(realm):
        """Check for managed namespace"""
        return realm.find('NameSpaceType').text == 'Managed'

    @staticmethod
    def get_login(realm):
        """Get the login domain from the realm XML"""
        domain = realm.find('CloudInstanceName').text
        return f'https://login.{domain}/extSTS.srf'

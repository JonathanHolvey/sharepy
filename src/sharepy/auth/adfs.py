from getpass import getpass
from datetime import datetime, timedelta
from xml.sax.saxutils import escape
import xml.etree.ElementTree as et
from uuid import uuid4

import requests

from .base import BaseAuth
from .xml import namespaces as ns
from . import templates
from .. import errors

MSO_AUTH_URL = 'https://login.microsoftonline.com/rst2.srf'


class SharePointADFS(BaseAuth):
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
        """Request authentication token from ADFS server"""
        # Generate timestamps and GUID
        created = datetime.utcnow()
        expires = created + timedelta(minutes=10)
        message_id = str(uuid4())

        # Define headers to request the token
        headers = {'Content-Type': 'application/soap+xml; charset=utf-8'}

        # Insert variables into SAML request
        password = self.password or getpass('Enter your password: ')
        saml = templates.load('adfs-assertion.saml').format(username=escape(self.username),
                                                            password=escape(password),
                                                            login_url=self.login_url,
                                                            message_id=message_id,
                                                            created=created.isoformat() + 'Z',
                                                            expires=expires.isoformat() + 'Z')

        # Request security token from Microsoft Online
        response = requests.post(self.login_url, data=saml, headers=headers)
        # Parse and extract assertion from returned XML
        try:
            root = et.fromstring(response.text)
        except et.ParseError:
            raise errors.AuthError('Token request failed. Invalid server response')

        # Extract token from returned XML
        assertion = root.find('.//saml:Assertion', ns)
        if assertion is None or root.find('.//S:Fault', ns) is not None:
            print(response.text)
            raise errors.AuthError.fromxml(root)

        assertion.set('xs', ns['xs'])  # Add namespace for assertion values
        saml_assertion = et.tostring(assertion, encoding='unicode')

        # Get the BinarySecurityToken
        saml = templates.load('adfs-token.saml').format(assertion=saml_assertion,
                                                        endpoint='sharepoint.com')
        response = requests.post(url=MSO_AUTH_URL, data=saml, headers=headers)
        # Parse and extract token from returned XML
        try:
            root = et.fromstring(response.text)
            token = root.find('.//wsse:BinarySecurityToken', ns).text
        except (AttributeError, et.ParseError):
            raise errors.AuthError('Token request failed. Invalid server response')

        self.token = token
        return True

    def _get_cookie(self):
        idcrl_url = f'https://{self.site}/_vti_bin/idcrl.svc/'
        headers = {'Authorization': 'BPOSIDCRL ' + self.token,
                   'X-IDCRL_ACCEPTED': 't',
                   'User-Agent': ''}
        response = requests.get(url=idcrl_url, headers=headers)

        if response.status_code == requests.codes.ok:
            # Add the IDCRL cookie to the session
            self.cookie = self._buildcookie(response.cookies)
            return True
        else:
            raise errors.AuthError('ADFS Authentication failed')

    def _get_digest(self):
        """Check and refresh sites cookie and request digest"""
        if self.expire <= datetime.now():
            # Request site context info from SharePoint site
            request_url = f'https://{self.site}/_vti_bin/sites.asmx'
            headers = ({'SOAPAction': 'http://schemas.microsoft.com/'
                       'sharepoint/soap/GetUpdatedFormDigestInformation',
                        'Host': self.site,
                        'Content-Type': 'text/xml;charset=utf-8',
                        'Cookie': self.cookie,
                        'X-RequestForceAuthentication': 'true'})
            digest_envelope = templates.load('adfs-digest.saml')
            response = requests.post(request_url, data=digest_envelope, headers=headers)

            # Parse digest text and timeout from XML
            try:
                root = et.fromstring(response.text)
                self.digest = root.find('.//soap:DigestValue', ns).text
                timeout = int(root.find('.//soap:TimeoutSeconds', ns).text)
            except (AttributeError, et.ParseError):
                raise errors.AuthError('Digest request failed')

            # Calculate digest expiry time
            self.expire = datetime.now() + timedelta(seconds=timeout)

    def _buildcookie(self, cookies):
        """Create session cookie from response cookie dictionary"""
        return 'SPOIDCRL=' + cookies['SPOIDCRL']

    @staticmethod
    def supports(realm):
        """Check for managed namespace"""
        return realm.find('NameSpaceType').text == 'Federated'

    @staticmethod
    def get_login(realm):
        """Get the login URL from the realm XML"""
        return realm.find('STSAuthURL').text

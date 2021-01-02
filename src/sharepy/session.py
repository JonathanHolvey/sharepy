import os
import re
import pickle

import requests

from . import __version__
from . import auth
from . import errors


def connect(site, username=None, password=None):
    username = username or input('Enter your username: ')
    autoauth = auth.detect(username=username, password=password)
    return SharePointSession(site, auth=autoauth)


def load(filename='sp-session.pkl'):
    """Load and return saved session object"""
    session = SharePointSession()
    with open(filename, 'rb') as file:
        session.__dict__.update(pickle.load(file))
    # Check session version
    if not session._check():
        raise errors.SessionError('The session is not compatible with the current SharePy version')

    # Try to authenticate the saved session
    if session.auth.refresh() or session.auth.login():
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
      >>> s = sharepy.connect('example.sharepoint.com')
      >>> s.get('https://example.sharepoint.com/_api/web/lists')
      <Response [200]>
    """

    def __init__(self, site=None, auth=None):
        super().__init__()
        self.version = __version__

        if site is not None:
            self.site = re.sub(r'^https?://', '', site)
            self.auth = auth
            self.headers.update({
                'Accept': 'application/json; odata=verbose',
                'Content-type': 'application/json; odata=verbose'
            })
            self.auth.login(self.site)

    def save(self, filename='sp-session.pkl'):
        """Serialise session object and save to file"""
        mode = 'r+b' if os.path.isfile(filename) else 'wb'
        with open(filename, mode) as file:
            pickle.dump(self.__dict__, file)

    def getfile(self, url, *args, **kwargs):
        """Stream download of specified URL and output to file"""
        # Extract file name from request URL if not provided as keyword argument
        filename = kwargs.pop('filename', re.search(r'[^/]+$', url).group(0))
        kwargs['stream'] = True
        # Request file in stream mode
        response = self.get(url, *args, **kwargs)
        # Save to output file
        if response.status_code == requests.codes.ok:
            with open(filename, 'wb') as file:
                for chunk in response:
                    file.write(chunk)
        return response

    def _check(self):
        """Compare the the current major version against the stored value"""
        try:
            valid = self.version.split('.')[0] == __version__.split('.')[0]
        except AttributeError:
            return False
        return valid

import xml.etree.ElementTree as et
from xml.sax.saxutils import escape

import requests

from .spol import SharePointOnline
from .adfs import SharePointADFS
from .. import errors

auth_classes = [
    SharePointOnline.__name__,
    SharePointADFS.__name__,
]


def detect(username, password=None):
    """Detect the correct auth class to use for a SharePoint login"""
    url = "https://login.microsoftonline.com/GetUserRealm.srf?login={}&xml=1"
    realm = et.fromstring(requests.get(url.format(escape(username))).text)

    for class_name in auth_classes:
        _class = globals()[class_name]
        # Check that the current class supports the realm
        if not _class.supports(realm):
            continue
        # Get the login URL from the realm XML
        login_url = _class.get_login(realm)
        return _class(username, password, login_url=login_url)

    auth_type = realm.find("NameSpaceType").text
    raise errors.AuthError("'{}' namespace sites are not supported".format(auth_type))

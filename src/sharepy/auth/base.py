from datetime import datetime
import xml.etree.ElementTree as et

import requests


class BaseAuth(requests.auth.AuthBase):
    """A base interface that all SharePy auth classes should inherit from"""
    def __init__(self, username, password=None, auth_url=None):
        self.site = None
        self.username = username
        self.password = password
        self.auth_url = auth_url or self.auth_url
        self.expire = datetime.now()

    def login(self, site):
        """Perform authentication steps"""
        raise NotImplementedError("Please implement this method")

    def refresh(self):
        """Refresh any expiring"""
        raise NotImplementedError("Please implement this method")


class SoapAuth(BaseAuth):
    xml = et
    ns = {
        "d": "http://schemas.microsoft.com/ado/2007/08/dataservices",
        "ds": "http://www.w3.org/2000/09/xmldsig#",
        "ec": "http://www.w3.org/2001/10/xml-exc-c14n#",
        "psf": "http://schemas.microsoft.com/Passport/SoapServices/SOAPFault",
        "S": "http://www.w3.org/2003/05/soap-envelope",
        "saml": "urn:oasis:names:tc:SAML:1.0:assertion",
        "soap": "http://schemas.microsoft.com/sharepoint/soap/",
        "wsse": "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd",
        "xs": "http://www.w3.org/2001/XMLSchema",
        "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    }

    def __init__(self, *args, **kwargs):
        super()
        # Register XML namespaces
        for alias, uri in self.ns.items():
            self.xml.register_namespace(alias, uri)

from .auth.xml import namespaces as ns


class AuthError(Exception):
    def __init__(self, message):
        self.message = message

    @staticmethod
    def fromxml(xml):
        """Parse an error message from SAML token response XML"""
        try:
            title = xml.find(".//S:Text", ns).text
            description = xml.find(".//psf:text", ns).text
            message = f'{title}: {description}'.strip('.')
        except AttributeError:
            message = 'Unknown authentication error'
        return AuthError(message)


class SessionError(Exception):
    def __init__(self, message):
        self.message = message


class AuthError(Exception):
    def __init__(self, message):
        self.message = message


class AuthTypeError(Exception):
    def __init__(self, message):
        self.message = message


class TokenError(Exception):
    def __init__(self, message):
        self.message = message


class DigestError(Exception):
    def __init__(self, message):
        self.message = message

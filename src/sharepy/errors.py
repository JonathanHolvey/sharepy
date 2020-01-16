
class AuthError(Exception):
    def __init__(self, message):
        self.message = message


class SessionError(Exception):
    def __init__(self, message):
        self.message = message

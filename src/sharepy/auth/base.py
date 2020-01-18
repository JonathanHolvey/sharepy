from requests.auth import AuthBase as RequestsAuth


class BaseAuth(RequestsAuth):
    site = None

    """A base interface that all SharePy auth classes should inherit from"""
    def __init__(self, username, password=None):
        self.username = username
        self.password = password

    def login(self, site):
        """Perform authentication steps"""
        raise NotImplementedError("Auth classes must allow login")

    def refresh(self):
        """Refresh any expiring tokens or cookies"""
        raise NotImplementedError("Auth classes must allow refresh")

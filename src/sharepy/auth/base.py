from requests.auth import AuthBase as RequestsAuth


class BaseAuth(RequestsAuth):
    """A base interface that all SharePy auth classes should inherit from"""
    site = None

    def __init__(self, username, password=None, login_url=None):
        self.username = username
        self.password = password
        self.login_url = login_url
        self.cookie = None
        self.digest = None

    def __call__(self, request):
        """Inject auth cookies into requests"""
        if self.cookie and self.digest:
            request.headers.update({'Cookie': self.cookie,
                                    'X-RequestDigest': self.digest})
        return request

    def login(self, site):
        """Perform authentication steps"""
        raise NotImplementedError('Auth classes must implement login')

    def refresh(self):
        """Refresh any expiring tokens or cookies"""
        raise NotImplementedError('Auth classes must implement refresh')

    @staticmethod
    def supports(realm):
        """Check if the class supports the provided auth realm"""
        raise NotImplementedError('Auth classes must implement supports')

    @staticmethod
    def get_login(realm):
        """Get the login URL from the realm XML"""
        raise NotImplementedError('Auth classes must implement get_login')

"""
Greenhouse Authenticator.

Greenhouse job boards typically don't require authentication for public job listings.
"""

from authenticator import AIHawkAuthenticator


class GreenhouseAuthenticator(AIHawkAuthenticator):
    """
    Authenticator for Greenhouse job portal.
    Greenhouse typically uses session-based authentication for internal use.
    Public job boards don't require authentication.
    """

    def __init__(self, driver):
        super().__init__(driver)

    @property
    def home_url(self):
        return "https://boards.greenhouse.io"

    def navigate_to_login(self):
        # Greenhouse public boards don't require login
        pass

    def handle_security_checks(self):
        # No specific security checks for public boards
        pass

    @property
    def is_logged_in(self):
        # Public boards are always accessible
        return True

    def start(self):
        # No authentication needed for public job boards
        pass

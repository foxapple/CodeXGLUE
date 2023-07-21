from github import Github
from django.contrib.auth.models import User
from tools.decorators import extend


@extend(User)
class Profile(object):
    """Add shortcuts to user"""

    @property
    def github(self):
        """Github api instance with access from user"""
        return Github(self.github_token)

    @property
    def github_token(self):
        """Get github api token"""
        return self.social_auth.get().extra_data['access_token']

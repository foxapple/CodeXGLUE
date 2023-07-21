from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    birthday = models.DateField(blank=True, null=True)
    provider = models.ForeignKey("providers.Provider", blank=True, null=True, related_name="owners")

    def is_provider(self):
        return self.provider is not None

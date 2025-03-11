from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    birthdate = models.DateField()
    stripe_customer_id = models.CharField(max_length=255, blank=True)

    # TODO: This should be more secure
    google_cli_key = models.TextField(blank=True)

    def __str__(self):
        return self.user.username

from django.db import models
from django.contrib.auth.models import AbstractUser

# Custom User Model for Buyer and Seller types
class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('buyer', 'Buyer'),
        ('seller', 'Seller'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)

    def is_admin(self):
        return self.is_superuser  # Check if the user is an admin


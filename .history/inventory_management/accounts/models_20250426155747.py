from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES =(
        ('admin','Admin'),
        ('buyer','Buyer'),
        ('seller','Seller'),
    )
    user_type =models.CharField(max_length=10,choices=USER_TYPE_CHOICES)
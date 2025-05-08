from django.db import models
from django.contrib.auth.models import AbstractUser

# Custom User Model for Buyer and Seller types
class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('buyer', 'Buyer'),
        ('supplier', 'Supplier'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)

    def is_admin(self):
        return self.is_superuser  # Check if the user is an admin

class Buyer(models.Model):
    full_name=models.CharField(max_length=100)
    address = models.TextField()
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=100,unique=True)
    password =models.CharField(max_length=128) #store hashed password
    last_login = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.full_name

class Supplier(models.Model):
    full_name=models.CharField(max_length=100)
    address = models.TextField()
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=100,unique=True)
    password =models.CharField(max_length=128) #store hashed password
    date_joined = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.full_name        

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
import os
import uuid
from django.utils.deconstruct import deconstructible

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
    last_login = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.full_name        

class Season(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

#for creating unique file name for image so that no override occurs
@deconstructible
class UniqueFileName:
    def __init__(self, subdir):
        self.subdir = subdir

    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        unique_filename = f"{uuid.uuid4().hex}.{ext}"
        return os.path.join(self.subdir, unique_filename)

class Product(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL,null=True, blank=True)
    season = models.ForeignKey(Season, on_delete=models.SET_NULL, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2,validators=[MinValueValidator(0.01)])
    quantity = models.PositiveIntegerField()
    picture = models.ImageField(upload_to='product_images/', null=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)  # Now optional

    def __str__(self):
        return self.name

class Order(models.Model):
    buyer = models.ForeignKey(Buyer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    order_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.buyer.name} - {self.product.name}"

class Delivery(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    delivery_date = models.DateField()
    status = models.CharField(max_length=50)

    def __str__(self):
        return f"Delivery for {self.order}"        

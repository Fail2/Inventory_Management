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

class Product(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    supplier = models.ForeignKey('Supplier', on_delete=models.CASCADE)
    season = models.ForeignKey('Season', on_delete=models.CASCADE, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    picture = models.ImageField(upload_to='product_images/', null=True, blank=True)

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

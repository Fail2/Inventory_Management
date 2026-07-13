from decimal import Decimal

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.utils import timezone
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
    last_login = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.full_name

class Supplier(models.Model):
    full_name=models.CharField(max_length=100)
    address = models.TextField()
    email = models.EmailField(unique=True)
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
    picture = models.ImageField(upload_to=UniqueFileName('product_images/'), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    def save(self, *args, **kwargs):
        try:
            this = Product.objects.get(id=self.id)
            if this.picture and self.picture != this.picture:
                this.picture.delete(save=False)
        except Product.DoesNotExist:
            pass  # This is a new product, no need to delete anything

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.picture:
            self.picture.delete(save=False)
        super().delete(*args, **kwargs)


class OrderGroup(models.Model):
    """One checkout = one OrderGroup, holding one OrderItem per product line."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
    ]
    buyer = models.ForeignKey(Buyer, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    delivery_address = models.TextField(blank=False)
    phone_number = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    order_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.buyer.full_name}"

    @property
    def total_amount(self):
        return sum((item.line_total for item in self.items.all()), Decimal('0.00'))


class OrderItem(models.Model):
    order = models.ForeignKey(OrderGroup, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity

#one-time passcode used for passwordless buyer/supplier login
class EmailOTP(models.Model):
    ROLE_CHOICES = (
        ('buyer', 'Buyer'),
        ('supplier', 'Supplier'),
    )
    email = models.EmailField()
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='buyer')
    code_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)

    MAX_ATTEMPTS = 5

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"OTP for {self.email} ({self.role})"

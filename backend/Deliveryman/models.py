from django.db import models

# Create your models here.
# models.py
from django.contrib.auth.models import User
from django.db import models

class Deliveryman(models.Model):
    phone_number = models.CharField(max_length=15, unique=True)
    vehicle_type = models.CharField(max_length=50, choices=[("Bike", "Bike"), ("Car", "Car"), ("Van", "Van")])
    profile_picture = models.ImageField(upload_to="deliveryman_profiles/", blank=True, null=True)
    is_verified = models.BooleanField(default=False)  # Admin verification
    is_available = models.BooleanField(default=True)  # Can accept orders

    def __str__(self):
        return self.username
    
# models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Order(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    deliveryman = models.ForeignKey("Deliveryman", on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")
    status = models.CharField(
        max_length=20, choices=[("Pending", "Pending"), ("Assigned", "Assigned"), ("Delivered", "Delivered")], default="Pending"
    )
    pickup_address = models.TextField()
    dropoff_address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} - {self.status}"


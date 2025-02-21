from django.db import models
from django.contrib.auth.models import User


# Restaurant details model. Restaurants will use these details to login

class Restaurant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="restaurantUser", default=None, blank=True)
    name = models.CharField(max_length=64)
    address = models.TextField()
    image = models.ImageField(upload_to="restaurant_images", blank=True, null=True)

    def __str__(self):
        return f"{self.user} : {self.name}"


# Stripe model to store the stripe account ID of restaurants
class Stripe(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='restaurantStripe')
    accountID = models.CharField(max_length=32)

    def __str__(self):
        return f"{self.restaurant}"


# Model for the food item.
    
class FoodItem(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE,related_name="restaurant")
    name = models.CharField(max_length=32)
    description = models.TextField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    image = models.ImageField(upload_to="food_images", blank=True, null=True)

    def __str__(self):
        return f"{self.name}"
    


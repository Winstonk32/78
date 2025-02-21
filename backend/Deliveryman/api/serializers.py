# serializers.py
from rest_framework import serializers
from Deliveryman.models import Deliveryman, Order

class DeliverymanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deliveryman
        fields = ["id", "username", "email", "phone_number", "vehicle_type", "is_verified", "is_available"]

class OrderSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source="restaurant.name", read_only=True)
    customer_name = serializers.CharField(source="customer.username", read_only=True)
    deliveryman_name = serializers.CharField(source="deliveryman.username", read_only=True, allow_null=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "restaurant_name",
            "customer_name",
            "deliveryman_name",
            "status",
            "total_price",
            "created_at",
            "updated_at",
            "delivery_address",
        ]
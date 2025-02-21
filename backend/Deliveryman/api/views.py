from django.shortcuts import render

# Create your views here.

# views.py
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from Deliveryman.models import Deliveryman
from .serializers import DeliverymanSerializer
from rest_framework.decorators import api_view
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod

    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['username'] = user.username

        if user.groups.filter(name="Deliveryman").exists():
            token['group'] = "Deliveryman"
            
        else:
            token['group'] = "None"

        # ...
        return token


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


# Rider Registration
# ✅ Rider Registration (Only Accepts POST)

from django.contrib.auth.models import Group
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

class RegisterDeliveryman(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")

        if not username or not email or not password:
            return Response({"error": "All fields are required"}, status=400)

        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already taken"}, status=400)

        user = User.objects.create(
            username=username,
            email=email,
            password=make_password(password)  # Hash the password before saving
        )

        # Create Deliveryman profile
        deliveryman = Deliveryman.objects.create(user=user)

        # Generate a token
        token, created = Token.objects.get_or_create(user=user)

        return Response({
            "message": "Deliveryman registered successfully",
            "token": token.key,
            "user_id": user.id,
            "username": user.username
        }, status=201)



from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import permissions
from django.contrib.auth import get_user_model
from Deliveryman.models import Deliveryman

User = get_user_model()

class LoginDeliveryman(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response({"error": "Username and password are required"}, status=400)

        user = authenticate(username=username, password=password)  # Authenticate

        if user is None:
            return Response({"error": "Invalid credentials"}, status=400)

        # Ensure the user is a Deliveryman
        try:
            deliveryman = Deliveryman.objects.get(user=user)
        except Deliveryman.DoesNotExist:
            return Response({"error": "Not a registered deliveryman"}, status=400)

        token, created = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user_id": user.id, "username": user.username})

    
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from Deliveryman.models import Order
from .serializers import OrderSerializer
class AvailableOrders(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Fetch orders that are not yet assigned to a rider
        orders = Order.objects.filter(deliveryman__isnull=True, status="Pending")
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

class ClaimOrder(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        order = Order.objects.get(id=order_id)

        if order.deliveryman is None:
            order.deliveryman = request.user  # Assign the logged-in rider
            order.status = "Assigned"
            order.save()
            return Response({"message": "Order claimed successfully"})
        return Response({"error": "Order already taken"}, status=400)

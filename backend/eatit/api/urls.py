from django.urls import path
from . import views
from .views import MyTokenObtainPairView

# Refer to: https://django-rest-framework-simplejwt.readthedocs.io/en/latest/getting_started.html#installation 
# for installation of JWT with DRF

from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

# Refer to the corresponding view function for more detials of the url routes
urlpatterns = [ 
    # To display a list of available API routes through DRF
    path('', views.getRoutes, name="index"),

    # User authentication
    path('api/register/', views.register, name="register" ),


    # To get all the restaurants, and their data (food, information)
    path('restaurants/', views.restaurants, name="restaurants"),
    path('restaurants/<int:id>', views.restaurantsFood, name="restaurantsFood"),
    path('restaurants/info/<int:id>', views.restaurantsInfo, name="restaurantsInfo"),
    
    # To get, add or remove item(s) from user's cart
    path('get-cart-items/', views.getCartItems, name="getCartItems"),
    path('add-to-cart/<int:id>', views.addToCart, name="addToCart"),
    path('remove-from-cart/<int:id>', views.removeFromCart, name="removeFromCart"),

    # To add a user's address, and to get all the address added by the user
    path('add-address/', views.addAddress, name='addAddress'),
    path('get-address/', views.getAddress, name='getAddress'),

    # To place an order, to get a user's existing orders, and to get the logged in user's info
    path('checkout/', views.checkout, name='checkout'),
    path('get-orders/', views.getOrders, name='getOrders'),
    path('get-user-info/', views.getUserInfo, name='getUserInfo'),
    path('update-user/', views.update_user, name='updateuser'),

    # For user authentication
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('custom-login/', views.customLogin, name='customLogin'),
]

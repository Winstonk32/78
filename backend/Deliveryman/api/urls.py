# urls.py
from django.urls import path
from .views import RegisterDeliveryman, LoginDeliveryman

from rest_framework_simplejwt.views import TokenRefreshView
from .views import MyTokenObtainPairView

urlpatterns = [
    path("deliveryregister/", RegisterDeliveryman.as_view(), name="register-deliveryman"),
    path("deliverylogin/", LoginDeliveryman.as_view(), name="login-deliveryman"),
    path("token/", MyTokenObtainPairView.as_view(), name="token_obtain_pair"),  # Custom login
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),  # Token refresh
]

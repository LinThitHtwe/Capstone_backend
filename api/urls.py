from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import auth_views, views

app_name = "api"

urlpatterns = [
    path("health/", views.health, name="health"),
    path("auth/signup/", auth_views.SignupView.as_view(), name="signup"),
    path("auth/login/", auth_views.LoginView.as_view(), name="login"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("admin/me/", auth_views.AdminMeView.as_view(), name="admin_me"),
]

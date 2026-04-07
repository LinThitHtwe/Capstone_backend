from django.urls import path, re_path
from rest_framework_simplejwt.views import TokenRefreshView

from . import auth_views, views

app_name = "api"

urlpatterns = [
    re_path(r"^health/?$", views.health, name="health"),
    # Optional trailing slash so POSTs never hit APPEND_SLASH (which cannot redirect POST).
    re_path(r"^auth/signup/?$", auth_views.SignupView.as_view(), name="signup"),
    re_path(r"^auth/login/?$", auth_views.LoginView.as_view(), name="login"),
    re_path(r"^auth/token/refresh/?$", TokenRefreshView.as_view(), name="token_refresh"),
    re_path(r"^admin/me/?$", auth_views.AdminMeView.as_view(), name="admin_me"),
]

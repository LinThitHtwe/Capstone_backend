from django.urls import path, re_path
from rest_framework_simplejwt.views import TokenRefreshView

from . import admin_views, auth_views, views

app_name = "api"

urlpatterns = [
    re_path(r"^health/?$", views.health, name="health"),
    # Optional trailing slash so POSTs never hit APPEND_SLASH (which cannot redirect POST).
    re_path(r"^auth/signup/?$", auth_views.SignupView.as_view(), name="signup"),
    re_path(r"^auth/login/?$", auth_views.LoginView.as_view(), name="login"),
    re_path(r"^auth/token/refresh/?$", TokenRefreshView.as_view(), name="token_refresh"),
    re_path(r"^admin/me/?$", auth_views.AdminMeView.as_view(), name="admin_me"),
    re_path(
        r"^admin/tables/?$",
        admin_views.AdminTableListCreateView.as_view(),
        name="admin_tables",
    ),
    re_path(
        r"^admin/tables/(?P<pk>\d+)/?$",
        admin_views.AdminTableDetailView.as_view(),
        name="admin_table_detail",
    ),
]

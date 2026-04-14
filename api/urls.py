from django.urls import path, re_path
from rest_framework_simplejwt.views import TokenRefreshView

from . import admin_views, auth_views, user_reservation_views, views

app_name = "api"

urlpatterns = [
    re_path(r"^health/?$", views.health, name="health"),
    re_path(
        r"^iot/table-status/(?P<table_number>\d+)/?$",
        views.IoTTableStatusDetailView.as_view(),
        name="iot_table_status",
    ),
    re_path(
        r"^tables/?$",
        views.PublicTableListView.as_view(),
        name="public_tables",
    ),
    re_path(
        r"^public/tables/(?P<table_number>\d+)/weight-availability/?$",
        views.PublicTableWeightAvailabilityView.as_view(),
        name="public_table_weight_availability",
    ),
    re_path(
        r"^map-reservations/?$",
        views.PublicMapReservationListView.as_view(),
        name="public_map_reservations",
    ),
    re_path(
        r"^me/reservations/?$",
        user_reservation_views.UserReservationListCreateView.as_view(),
        name="user_reservations",
    ),
    # Optional trailing slash so POSTs never hit APPEND_SLASH (which cannot redirect POST).
    re_path(r"^auth/signup/?$", auth_views.SignupView.as_view(), name="signup"),
    re_path(r"^auth/login/?$", auth_views.LoginView.as_view(), name="login"),
    re_path(r"^auth/token/refresh/?$", TokenRefreshView.as_view(), name="token_refresh"),
    re_path(r"^admin/me/?$", auth_views.AdminMeView.as_view(), name="admin_me"),
    re_path(
        r"^admin/students/?$",
        admin_views.AdminStudentListView.as_view(),
        name="admin_students",
    ),
    re_path(
        r"^admin/students/(?P<pk>\d+)/?$",
        admin_views.AdminStudentDetailView.as_view(),
        name="admin_student_detail",
    ),
    re_path(
        r"^admin/staff/?$",
        admin_views.AdminStaffListView.as_view(),
        name="admin_staff",
    ),
    re_path(
        r"^admin/staff/(?P<pk>\d+)/?$",
        admin_views.AdminStaffDetailView.as_view(),
        name="admin_staff_detail",
    ),
    re_path(
        r"^admin/lecturers/?$",
        admin_views.AdminLecturerListView.as_view(),
        name="admin_lecturers",
    ),
    re_path(
        r"^admin/lecturers/(?P<pk>\d+)/?$",
        admin_views.AdminLecturerDetailView.as_view(),
        name="admin_lecturer_detail",
    ),
    re_path(
        r"^admin/visitors/?$",
        admin_views.AdminVisitorListView.as_view(),
        name="admin_visitors",
    ),
    re_path(
        r"^admin/visitors/(?P<pk>\d+)/?$",
        admin_views.AdminVisitorDetailView.as_view(),
        name="admin_visitor_detail",
    ),
    re_path(
        r"^admin/reservations/?$",
        admin_views.AdminReservationListView.as_view(),
        name="admin_reservations",
    ),
    re_path(
        r"^admin/reservations/(?P<pk>\d+)/?$",
        admin_views.AdminReservationDetailView.as_view(),
        name="admin_reservation_detail",
    ),
    re_path(
        r"^admin/weight-sensors/?$",
        admin_views.AdminWeightSensorListCreateView.as_view(),
        name="admin_weight_sensors",
    ),
    re_path(
        r"^admin/weight-sensors/(?P<pk>\d+)/?$",
        admin_views.AdminWeightSensorDetailView.as_view(),
        name="admin_weight_sensor_detail",
    ),
    re_path(
        r"^admin/lcd-displays/?$",
        admin_views.AdminLCDDisplayListCreateView.as_view(),
        name="admin_lcd_displays",
    ),
    re_path(
        r"^admin/lcd-displays/(?P<pk>\d+)/?$",
        admin_views.AdminLCDDisplayDetailView.as_view(),
        name="admin_lcd_display_detail",
    ),
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

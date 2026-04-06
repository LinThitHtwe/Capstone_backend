from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import LCDDisplay, OccupancyEvent, Reservation, Table, User, WeightSensor


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("email",)
    list_display = ("email", "name", "role", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active", "role")
    search_fields = ("email", "name", "id_number")
    readonly_fields = ("last_login", "date_joined")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Profile"), {"fields": ("name", "role", "id_number", "date_joined")}),
        (
            _("Permissions"),
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        (_("Important dates"), {"fields": ("last_login",)}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "name",
                    "role",
                    "id_number",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )


admin.site.register(WeightSensor)
admin.site.register(Table)
admin.site.register(Reservation)
admin.site.register(LCDDisplay)
admin.site.register(OccupancyEvent)

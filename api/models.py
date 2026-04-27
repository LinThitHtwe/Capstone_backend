from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.base_user import BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from .constants import ROLE_ADMIN, TABLE_STATUS_FREE


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", ROLE_ADMIN)
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=64)
    id_number = models.CharField(max_length=64)
    date_joined = models.DateTimeField(default=timezone.now)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "role", "id_number"]

    objects = UserManager()

    class Meta:
        db_table = "User"

    def __str__(self):
        return self.email

    @property
    def is_admin(self) -> bool:
        return self.role == ROLE_ADMIN

    def save(self, *args, **kwargs):
        if self.role == ROLE_ADMIN:
            qs = User.objects.filter(role=ROLE_ADMIN)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError(
                    {"role": "Only one admin account is allowed in the system."}
                )
        super().save(*args, **kwargs)


class WeightSensor(models.Model):
    name = models.CharField(max_length=255)
    last_reading_at = models.DateTimeField(null=True, blank=True)
    is_available = models.BooleanField(default=True)

    class Meta:
        db_table = "weight_sensor"

    def __str__(self):
        return f"{self.name} ({self.pk})"


class Table(models.Model):
    table_number = models.IntegerField(unique=True)
    weight_sensor = models.ForeignKey(
        WeightSensor,
        on_delete=models.SET_NULL,
        db_column="weight_sensor_id",
        related_name="tables",
        null=True,
        blank=True,
    )
    is_reservable = models.BooleanField(default=True)
    table_type = models.CharField(max_length=64, db_column="type")
    library_floor = models.IntegerField()
    position_x = models.IntegerField()
    position_y = models.IntegerField()
    is_available = models.BooleanField(default=True)
    # 1=free, 2=occupied, 3=reserved — see ``api.constants`` (TABLE_STATUS_*).
    status = models.PositiveSmallIntegerField(default=TABLE_STATUS_FREE)

    class Meta:
        db_table = "Table"

    def __str__(self):
        return f"Table {self.table_number}"


class Reservation(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column="user_id",
        related_name="reservations",
    )
    table = models.ForeignKey(
        Table,
        on_delete=models.CASCADE,
        db_column="table_id",
        related_name="reservations",
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration_minutes = models.IntegerField()
    is_available = models.BooleanField(default=True)
    otp = models.CharField(max_length=32, blank=True)
    otp_verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    overstay_alert_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "reservations"

    def __str__(self):
        return f"Reservation {self.pk} ({self.table_id})"


class LCDDisplay(models.Model):
    lcd_type = models.CharField(max_length=64, db_column="type")
    table = models.OneToOneField(
        Table,
        on_delete=models.CASCADE,
        db_column="table_id",
        null=True,
        blank=True,
        related_name="lcd_display",
    )
    recorded_at = models.DateTimeField(null=True, blank=True)
    is_available = models.BooleanField(default=True)

    class Meta:
        db_table = "LCD_Display"

    def __str__(self):
        return f"LCD {self.pk} ({self.lcd_type})"


class OccupancyEvent(models.Model):
    weight_sensor = models.ForeignKey(
        WeightSensor,
        on_delete=models.CASCADE,
        db_column="weight_sensor_id",
        related_name="occupancy_events",
    )
    weight = models.DecimalField(max_digits=10, decimal_places=2)
    recorded_at = models.DateTimeField()
    event_type = models.CharField(max_length=64)

    class Meta:
        db_table = "occupancy_event"

    def __str__(self):
        return f"OccupancyEvent {self.pk} @ {self.recorded_at}"

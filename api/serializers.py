from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .constants import PUBLIC_SIGNUP_ROLES
from .models import LCDDisplay, Reservation, Table, WeightSensor

User = get_user_model()


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(
        choices=sorted(PUBLIC_SIGNUP_ROLES),
        help_text="One of: student, lecturer, staff, visitor (admin is not allowed).",
    )

    class Meta:
        model = User
        fields = (
            "email",
            "password",
            "password_confirm",
            "name",
            "id_number",
            "role",
        )

    def validate_role(self, value):
        if value not in PUBLIC_SIGNUP_ROLES:
            raise serializers.ValidationError("Invalid role for self-registration.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)


class UserMeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "name", "role", "id_number")


class AdminStudentSerializer(serializers.ModelSerializer):
    """Student accounts (and legacy ``member`` role); excludes admin and other roles."""

    class Meta:
        model = User
        fields = ("id", "email", "name", "id_number", "date_joined", "is_active")


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT claims include role/email; JSON body also returns ``user`` for redirect UX."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["email"] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserMeSerializer(self.user).data
        return data


class AdminWeightSensorSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeightSensor
        fields = ("id", "location", "last_reading_at", "is_available")
        read_only_fields = ("id", "last_reading_at")


class AdminLCDDisplaySerializer(serializers.ModelSerializer):
    table_id = serializers.PrimaryKeyRelatedField(
        source="table",
        queryset=Table.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = LCDDisplay
        fields = ("id", "lcd_type", "table_id", "recorded_at", "is_available")
        read_only_fields = ("id", "recorded_at")


class PublicTableSerializer(serializers.ModelSerializer):
    """Read-only layout for the public library map (no admin-only fields)."""

    class Meta:
        model = Table
        fields = (
            "id",
            "table_number",
            "table_type",
            "library_floor",
            "position_x",
            "position_y",
            "is_reservable",
            "is_available",
        )


class PublicMapReservationSerializer(serializers.ModelSerializer):
    """Minimal reservation slice for map colouring (no user PII)."""

    table_number = serializers.IntegerField(source="table.table_number", read_only=True)

    class Meta:
        model = Reservation
        fields = ("id", "table_number", "start_time", "end_time")


class AdminTableSerializer(serializers.ModelSerializer):
    # Table-only CRUD for now: sensor is optional.
    weight_sensor_id = serializers.PrimaryKeyRelatedField(
        source="weight_sensor",
        queryset=WeightSensor.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Table
        fields = (
            "id",
            "table_number",
            "table_type",
            "library_floor",
            "position_x",
            "position_y",
            "is_reservable",
            "is_available",
            "weight_sensor_id",
        )

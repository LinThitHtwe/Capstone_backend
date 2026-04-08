from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .constants import ROLE_MEMBER
from .models import Table, WeightSensor

User = get_user_model()


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("email", "password", "password_confirm", "name", "id_number")

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        validated_data["role"] = ROLE_MEMBER
        return User.objects.create_user(password=password, **validated_data)


class UserMeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "name", "role", "id_number")


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

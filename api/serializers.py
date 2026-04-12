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
    """Admin can name/link sensors; ``is_available`` is driven by hardware, not admin edits."""

    assigned_table = serializers.SerializerMethodField(read_only=True)
    table_id = serializers.PrimaryKeyRelatedField(
        queryset=Table.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = WeightSensor
        fields = (
            "id",
            "name",
            "last_reading_at",
            "is_available",
            "table_id",
            "assigned_table",
        )
        read_only_fields = ("id", "last_reading_at", "is_available", "assigned_table")

    @staticmethod
    def _sync_sensor_table(sensor, table):
        """Link is stored on ``Table.weight_sensor``; at most one table per sensor from admin."""
        Table.objects.filter(weight_sensor=sensor).update(weight_sensor=None)
        if table is not None:
            Table.objects.filter(pk=table.pk).update(weight_sensor_id=sensor.pk)

    def create(self, validated_data):
        table = validated_data.pop("table_id", serializers.empty)
        instance = super().create(validated_data)
        if table is not serializers.empty:
            self._sync_sensor_table(instance, table)
        return instance

    def update(self, instance, validated_data):
        table = validated_data.pop("table_id", serializers.empty)
        instance = super().update(instance, validated_data)
        if table is not serializers.empty:
            self._sync_sensor_table(instance, table)
        return instance

    def get_assigned_table(self, obj):
        tables = list(obj.tables.all())
        if not tables:
            return None
        t = tables[0]
        out = {
            "id": t.id,
            "table_number": t.table_number,
            "library_floor": t.library_floor,
        }
        extra = len(tables) - 1
        if extra > 0:
            out["also_linked_count"] = extra
        return out


class AdminLCDDisplaySerializer(serializers.ModelSerializer):
    """Admin edits type/table link; ``is_available`` is not editable via this API."""

    table_id = serializers.PrimaryKeyRelatedField(
        source="table",
        queryset=Table.objects.all(),
        required=False,
        allow_null=True,
    )
    assigned_table = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = LCDDisplay
        fields = (
            "id",
            "lcd_type",
            "table_id",
            "assigned_table",
            "recorded_at",
            "is_available",
        )
        read_only_fields = ("id", "recorded_at", "is_available", "assigned_table")

    def get_assigned_table(self, obj):
        t = obj.table
        if not t:
            return None
        return {
            "id": t.id,
            "table_number": t.table_number,
            "library_floor": t.library_floor,
        }

    def create(self, validated_data):
        table = validated_data.get("table")
        if table is not None:
            LCDDisplay.objects.filter(table=table).update(table=None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "table" in validated_data:
            new_table = validated_data["table"]
            if new_table is not None:
                LCDDisplay.objects.filter(table=new_table).exclude(pk=instance.pk).update(
                    table=None
                )
        return super().update(instance, validated_data)


class PublicTableSerializer(serializers.ModelSerializer):
    """Read-only layout for the public library map (no admin-only fields)."""

    sensor_seated = serializers.SerializerMethodField(read_only=True)

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
            "sensor_seated",
        )

    def get_sensor_seated(self, obj):
        """
        True when the linked weight sensor reads as occupied (not available).
        None when no sensor is assigned — clients may use a demo pattern.
        """
        ws = obj.weight_sensor
        if ws is None:
            return None
        return not ws.is_available


class PublicMapReservationSerializer(serializers.ModelSerializer):
    """Minimal reservation slice for map colouring (no user PII)."""

    table_number = serializers.IntegerField(source="table.table_number", read_only=True)

    class Meta:
        model = Reservation
        fields = ("id", "table_number", "start_time", "end_time")


class AdminReservationSerializer(serializers.ModelSerializer):
    """Admin reservation log with related user and table (read-only)."""

    user_id = serializers.IntegerField(source="user.id", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.CharField(source="user.name", read_only=True)
    table_id = serializers.IntegerField(source="table.id", read_only=True)
    table_number = serializers.IntegerField(source="table.table_number", read_only=True)

    class Meta:
        model = Reservation
        fields = (
            "id",
            "user_id",
            "user_email",
            "user_name",
            "table_id",
            "table_number",
            "start_time",
            "end_time",
            "duration_minutes",
            "is_available",
            "otp",
            "created_at",
            "reminder_sent_at",
            "overstay_alert_sent_at",
        )


class AdminTableSerializer(serializers.ModelSerializer):
    # Table-only CRUD for now: sensor is optional.
    weight_sensor_id = serializers.PrimaryKeyRelatedField(
        source="weight_sensor",
        queryset=WeightSensor.objects.all(),
        required=False,
        allow_null=True,
    )
    sensor_seated = serializers.SerializerMethodField(read_only=True)
    lcd_display = serializers.SerializerMethodField(read_only=True)
    lcd_display_id = serializers.IntegerField(
        write_only=True, required=False, allow_null=True
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
            "sensor_seated",
            "lcd_display",
            "lcd_display_id",
        )

    def get_sensor_seated(self, obj):
        ws = obj.weight_sensor
        if ws is None:
            return None
        return not ws.is_available

    def get_lcd_display(self, obj):
        lcd = LCDDisplay.objects.filter(table=obj).first()
        if not lcd:
            return None
        return {"id": lcd.id, "lcd_type": lcd.lcd_type}

    @staticmethod
    def _sync_lcd_display(table, lcd_display_id):
        LCDDisplay.objects.filter(table=table).update(table=None)
        if lcd_display_id is not None:
            LCDDisplay.objects.filter(pk=lcd_display_id).update(table_id=table.id)

    def create(self, validated_data):
        lcd_id = validated_data.pop("lcd_display_id", None)
        instance = super().create(validated_data)
        self._sync_lcd_display(instance, lcd_id)
        return instance

    def update(self, instance, validated_data):
        lcd_id = validated_data.pop("lcd_display_id", serializers.empty)
        instance = super().update(instance, validated_data)
        if lcd_id is not serializers.empty:
            self._sync_lcd_display(instance, lcd_id)
        return instance

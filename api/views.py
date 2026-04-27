"""Public and health API views."""

from datetime import timedelta
from zoneinfo import ZoneInfo

from django.db import transaction
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import generics, serializers, status
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .constants import (
    LIBRARY_RESERVATION_TZ,
    TABLE_STATUS_FREE,
    TABLE_STATUS_OCCUPIED,
    TABLE_STATUS_RESERVED,
)
from .models import Reservation, Table
from .serializers import (
    IoTTableStatusSerializer,
    PublicMapReservationSerializer,
    PublicTableSerializer,
)

_IOT_TABLE_NUMBER = OpenApiParameter(
    name="table_number",
    type=OpenApiTypes.INT,
    location=OpenApiParameter.PATH,
    description="Library table number (unique label), not the database row id.",
)


def _clear_stale_reserved_on_weight_table(table: Table, now) -> None:
    """If table is RESERVED but no booking still covers ``now``, set status FREE."""
    if table.weight_sensor_id is None:
        return
    if table.status != TABLE_STATUS_RESERVED:
        return
    if Reservation.objects.filter(
        table_id=table.pk,
        is_available=True,
        end_time__gt=now,
    ).exists():
        return
    Table.objects.filter(pk=table.pk, status=TABLE_STATUS_RESERVED).update(
        status=TABLE_STATUS_FREE
    )


@extend_schema(
    summary="Health check",
    tags=["Public"],
    responses={
        200: inline_serializer(
            name="HealthResponse",
            fields={
                "status": serializers.CharField(),
                "message": serializers.CharField(),
                "version": serializers.CharField(),
            },
        )
    },
)
@api_view(["GET"])
def health(request):
    """Simple JSON placeholder to verify the API is running."""
    return Response(
        {
            "status": "ok",
            "message": "Capstone REST API placeholder",
            "version": "0.0.0",
        }
    )


@extend_schema(summary="List public library tables", tags=["Public"])
class PublicTableListView(generics.ListAPIView):
    """Library map layout; readable without authentication."""

    permission_classes = [AllowAny]
    serializer_class = PublicTableSerializer
    pagination_class = None

    def get_queryset(self):
        return (
            Table.objects.select_related("weight_sensor")
            .all()
            .order_by("table_number")
        )


@extend_schema(
    summary="Weight-table live booking end (ST1 / sensor tables)",
    description=(
        "For a table linked to a weight sensor: if a reservation is active now "
        "(start ≤ now < end), returns that booking's **end** in library local time. "
        "Also returns the next/upcoming booking window (``end_time`` > now) for IoT "
        "OLED text and ``otp_verified`` for keypad flow."
    ),
    parameters=[_IOT_TABLE_NUMBER],
    responses={
        200: inline_serializer(
            name="PublicWeightTableAvailability",
            fields={
                "table_number": serializers.IntegerField(),
                "has_weight_sensor": serializers.BooleanField(),
                "current_booking_ends_at": serializers.CharField(
                    allow_null=True,
                    help_text="ISO-8601 end of active reservation, or null.",
                ),
                "current_booking_ends_local": serializers.CharField(
                    allow_null=True,
                    help_text="HH:MM:SS in library timezone when start ≤ now < end; else null.",
                ),
                "current_booking_starts_local": serializers.CharField(
                    allow_null=True,
                    help_text="HH:MM start of display booking (end > now), or null.",
                ),
                "current_booking_window_end_local": serializers.CharField(
                    allow_null=True,
                    help_text="HH:MM end of display booking (end > now), or null.",
                ),
                "otp_verified": serializers.BooleanField(
                    help_text="True if display booking exists and OTP was verified at the table."
                ),
            },
        ),
        404: inline_serializer(
            name="PublicWeightTableNotFound",
            fields={"detail": serializers.CharField()},
        ),
    },
    tags=["Public"],
)
class PublicTableWeightAvailabilityView(APIView):
    """GET /api/public/tables/<table_number>/weight-availability/"""

    permission_classes = [AllowAny]

    def get(self, request, table_number):
        try:
            tn = int(table_number)
        except (TypeError, ValueError):
            return Response(
                {"detail": "Invalid table number."},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            table = Table.objects.select_related("weight_sensor").get(table_number=tn)
        except Table.DoesNotExist:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        has_weight_sensor = table.weight_sensor_id is not None
        ends_at = None
        ends_local = None
        starts_local = None
        window_end_local = None
        otp_verified = False

        if has_weight_sensor:
            now = timezone.now()
            _clear_stale_reserved_on_weight_table(table, now)
            table.refresh_from_db(fields=["status"])

            lib_tz = ZoneInfo(LIBRARY_RESERVATION_TZ)
            # Next/current booking not yet ended (start time ignored for display/OLED).
            # IoT OTP verify still requires start_time <= now — see IoTVerifyReservationOtpView.
            display_booking = (
                Reservation.objects.filter(
                    table=table,
                    is_available=True,
                    end_time__gt=now,
                )
                .order_by("start_time")
                .first()
            )
            if display_booking is not None:
                starts_local = display_booking.start_time.astimezone(lib_tz).strftime(
                    "%H:%M"
                )
                window_end_local = display_booking.end_time.astimezone(lib_tz).strftime(
                    "%H:%M"
                )
                otp_verified = display_booking.otp_verified_at is not None
                ends_at = display_booking.end_time
                ends_local = display_booking.end_time.astimezone(lib_tz).strftime(
                    "%H:%M:%S"
                )

        return Response(
            {
                "table_number": table.table_number,
                "has_weight_sensor": has_weight_sensor,
                "current_booking_ends_at": ends_at.isoformat() if ends_at else None,
                "current_booking_ends_local": ends_local,
                "current_booking_starts_local": starts_local,
                "current_booking_window_end_local": window_end_local,
                "otp_verified": otp_verified,
            }
        )


@extend_schema(
    summary="Verify reservation OTP at weight table (IoT keypad)",
    parameters=[_IOT_TABLE_NUMBER],
    request=inline_serializer(
        name="IoTVerifyReservationOtpBody",
        fields={"otp": serializers.CharField(help_text="6-digit code from email.")},
    ),
    responses={
        200: inline_serializer(
            name="IoTVerifyReservationOtpOk",
            fields={
                "detail": serializers.CharField(),
                "current_booking_window_end_local": serializers.CharField(),
            },
        ),
        400: inline_serializer(
            name="IoTVerifyReservationOtpErr",
            fields={"detail": serializers.CharField()},
        ),
        404: inline_serializer(
            name="IoTVerifyReservationOtpNotFound",
            fields={"detail": serializers.CharField()},
        ),
    },
    tags=["IoT"],
)
class IoTVerifyReservationOtpView(APIView):
    """POST /api/iot/tables/<table_number>/verify-reservation-otp/"""

    permission_classes = [AllowAny]

    def post(self, request, table_number):
        try:
            tn = int(table_number)
        except (TypeError, ValueError):
            return Response(
                {"detail": "Invalid table number."},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            table = Table.objects.get(table_number=tn)
        except Table.DoesNotExist:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if table.weight_sensor_id is None:
            return Response(
                {"detail": "This table does not use OTP check-in."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        otp_raw = request.data.get("otp")
        if otp_raw is None:
            return Response(
                {"detail": "Provide a 6-digit numeric OTP in JSON field `otp`."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        otp_val = str(otp_raw).strip()
        if len(otp_val) != 6 or not otp_val.isdigit():
            return Response(
                {"detail": "Provide a 6-digit numeric OTP in JSON field `otp`."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        now = timezone.now()
        lib_tz = ZoneInfo(LIBRARY_RESERVATION_TZ)
        with transaction.atomic():
            # Demo-friendly: allow early check-in before scheduled start (same row as
            # GET weight-availability display_booking: earliest start among not ended).
            res = (
                Reservation.objects.select_for_update()
                .filter(
                    table=table,
                    is_available=True,
                    end_time__gt=now,
                    otp_verified_at__isnull=True,
                )
                .order_by("start_time")
                .first()
            )
            if res is None:
                return Response(
                    {
                        "detail": "No upcoming or active reservation needs OTP verification."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            stored = (res.otp or "").strip()
            if stored != otp_val:
                return Response(
                    {"detail": "Incorrect OTP."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            res.otp_verified_at = now
            res.save(update_fields=["otp_verified_at"])
            Table.objects.filter(pk=table.pk).update(status=TABLE_STATUS_OCCUPIED)
        end_local = res.end_time.astimezone(lib_tz).strftime("%H:%M")
        return Response(
            {
                "detail": "ok",
                "current_booking_window_end_local": end_local,
            }
        )


class IoTTableStatusDetailView(APIView):
    """
    IoT-friendly table status for one table (no auth).

    Path segment is **``table_number``** (the library table label, unique), not DB ``id``.

    - **GET** ``/api/iot/table-status/<table_number>/`` — JSON ``{"status": <int>}``.
    - **POST** same URL — body ``{"status": <int>}``; response ``{"status": <int>}``.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        parameters=[_IOT_TABLE_NUMBER],
        responses={200: IoTTableStatusSerializer},
        tags=["IoT"],
    )
    def get(self, request, table_number):
        table = self._get_table(table_number)
        if table is None:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(IoTTableStatusSerializer(table).data)

    @extend_schema(
        parameters=[_IOT_TABLE_NUMBER],
        request=inline_serializer(
            name="IoTTableStatusUpdate",
            fields={
                "status": serializers.IntegerField(
                    help_text="1=free, 2=occupied, 3=reserved (app-defined)."
                ),
            },
        ),
        responses={200: IoTTableStatusSerializer},
        tags=["IoT"],
    )
    def post(self, request, table_number):
        table = self._get_table(table_number)
        if table is None:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        raw_st = request.data.get("status")
        try:
            new_status = int(raw_st)
        except (TypeError, ValueError):
            return Response(
                {"detail": "Expected integer `status` in JSON body."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if new_status < 0 or new_status > 65535:
            return Response(
                {"detail": "`status` out of allowed range."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        table.status = new_status
        table.save(update_fields=["status"])
        return Response(IoTTableStatusSerializer(table).data)

    def _get_table(self, table_number_str):
        try:
            tn = int(table_number_str)
        except (TypeError, ValueError):
            return None
        try:
            return Table.objects.get(table_number=tn)
        except Table.DoesNotExist:
            return None


@extend_schema(summary="List map-related reservations", tags=["Public"])
class PublicMapReservationListView(generics.ListAPIView):
    """
    Reservations that can affect the public map in the next 48 hours or are
    still active (end in the future). Omits user details.
    """

    permission_classes = [AllowAny]
    serializer_class = PublicMapReservationSerializer
    pagination_class = None

    def get_queryset(self):
        now = timezone.now()
        horizon = now + timedelta(hours=48)
        return (
            Reservation.objects.filter(
                is_available=True,
                end_time__gt=now,
                start_time__lte=horizon,
            )
            .select_related("table")
            .order_by("start_time")
        )

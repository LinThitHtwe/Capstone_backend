"""Public and health API views."""

from datetime import timedelta
from zoneinfo import ZoneInfo

from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import generics, serializers, status
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .constants import LIBRARY_RESERVATION_TZ
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
        "Used by the reserve page and IoT display instead of a hard-coded clock."
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
                    help_text="HH:MM:SS in library timezone, or null.",
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

        if has_weight_sensor:
            now = timezone.now()
            active = (
                Reservation.objects.filter(
                    table=table,
                    is_available=True,
                    start_time__lte=now,
                    end_time__gt=now,
                )
                .order_by("end_time")
                .first()
            )
            if active is not None:
                ends_at = active.end_time
                lib_tz = ZoneInfo(LIBRARY_RESERVATION_TZ)
                ends_local = active.end_time.astimezone(lib_tz).strftime("%H:%M:%S")

        return Response(
            {
                "table_number": table.table_number,
                "has_weight_sensor": has_weight_sensor,
                "current_booking_ends_at": ends_at.isoformat() if ends_at else None,
                "current_booking_ends_local": ends_local,
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

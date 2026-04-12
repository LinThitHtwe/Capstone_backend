"""Public and health API views."""

from datetime import timedelta

from django.utils import timezone
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Reservation, Table
from .serializers import PublicMapReservationSerializer, PublicTableSerializer


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

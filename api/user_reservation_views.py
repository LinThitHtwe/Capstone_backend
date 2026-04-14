"""Authenticated (non-admin) user reservation list and create."""

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.response import Response

from .models import Reservation
from .permissions import IsAuthenticatedNonAdmin
from .serializers import UserReservationCreateSerializer, UserReservationReadSerializer


@extend_schema_view(
    get=extend_schema(
        summary="List my reservations",
        tags=["User"],
        responses={200: UserReservationReadSerializer(many=True)},
    ),
    post=extend_schema(
        summary="Create a reservation",
        tags=["User"],
        request=UserReservationCreateSerializer,
        responses={201: UserReservationReadSerializer},
    ),
)
class UserReservationListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticatedNonAdmin]

    def get_queryset(self):
        return (
            Reservation.objects.filter(user=self.request.user)
            .select_related("table")
            .order_by("-start_time")
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return UserReservationCreateSerializer
        return UserReservationReadSerializer

    def create(self, request, *args, **kwargs):
        ser = UserReservationCreateSerializer(
            data=request.data, context={"request": request}
        )
        ser.is_valid(raise_exception=True)
        instance = ser.save()
        return Response(
            UserReservationReadSerializer(instance).data,
            status=status.HTTP_201_CREATED,
        )

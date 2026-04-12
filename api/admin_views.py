from django.contrib.auth import get_user_model
from django.db.models import Prefetch, Q
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination

from .constants import (
    ROLE_LECTURER,
    ROLE_MEMBER,
    ROLE_STAFF,
    ROLE_STUDENT,
    ROLE_VISITOR,
)
from .models import LCDDisplay, Reservation, Table, WeightSensor
from .permissions import IsAdminRole
from .serializers import (
    AdminLCDDisplaySerializer,
    AdminReservationSerializer,
    AdminStudentSerializer,
    AdminTableSerializer,
    AdminWeightSensorSerializer,
)

User = get_user_model()


class AdminStudentPagination(PageNumberPagination):
    page_size = 15
    page_size_query_param = "page_size"
    max_page_size = 100


class AdminStudentListView(generics.ListAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AdminStudentSerializer
    pagination_class = AdminStudentPagination

    def get_queryset(self):
        qs = User.objects.filter(role__in=(ROLE_STUDENT, ROLE_MEMBER))
        search = (self.request.query_params.get("search") or "").strip()
        if search:
            qs = qs.filter(
                Q(email__icontains=search)
                | Q(name__icontains=search)
                | Q(id_number__icontains=search)
            )
        ordering = self.request.query_params.get("ordering") or "-date_joined"
        allowed = {
            "name",
            "-name",
            "email",
            "-email",
            "id_number",
            "-id_number",
            "date_joined",
            "-date_joined",
            "id",
            "-id",
            "is_active",
            "-is_active",
        }
        if ordering in allowed:
            qs = qs.order_by(ordering)
        else:
            qs = qs.order_by("-date_joined")
        return qs


class AdminStudentDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AdminStudentSerializer
    queryset = User.objects.filter(role__in=(ROLE_STUDENT, ROLE_MEMBER))


def _admin_user_list_queryset_for_role(request, role: str):
    qs = User.objects.filter(role=role)
    search = (request.query_params.get("search") or "").strip()
    if search:
        qs = qs.filter(
            Q(email__icontains=search)
            | Q(name__icontains=search)
            | Q(id_number__icontains=search)
        )
    ordering = request.query_params.get("ordering") or "-date_joined"
    allowed = {
        "name",
        "-name",
        "email",
        "-email",
        "id_number",
        "-id_number",
        "date_joined",
        "-date_joined",
        "id",
        "-id",
        "is_active",
        "-is_active",
    }
    if ordering in allowed:
        qs = qs.order_by(ordering)
    else:
        qs = qs.order_by("-date_joined")
    return qs


class AdminStaffListView(generics.ListAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AdminStudentSerializer
    pagination_class = AdminStudentPagination

    def get_queryset(self):
        return _admin_user_list_queryset_for_role(self.request, ROLE_STAFF)


class AdminStaffDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AdminStudentSerializer
    queryset = User.objects.filter(role=ROLE_STAFF)


class AdminLecturerListView(generics.ListAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AdminStudentSerializer
    pagination_class = AdminStudentPagination

    def get_queryset(self):
        return _admin_user_list_queryset_for_role(self.request, ROLE_LECTURER)


class AdminLecturerDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AdminStudentSerializer
    queryset = User.objects.filter(role=ROLE_LECTURER)


class AdminVisitorListView(generics.ListAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AdminStudentSerializer
    pagination_class = AdminStudentPagination

    def get_queryset(self):
        return _admin_user_list_queryset_for_role(self.request, ROLE_VISITOR)


class AdminVisitorDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AdminStudentSerializer
    queryset = User.objects.filter(role=ROLE_VISITOR)


class AdminReservationListView(generics.ListAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AdminReservationSerializer
    pagination_class = AdminStudentPagination

    def get_queryset(self):
        qs = Reservation.objects.select_related("user", "table").all()
        search = (self.request.query_params.get("search") or "").strip()
        if search:
            q = (
                Q(user__email__icontains=search)
                | Q(user__name__icontains=search)
                | Q(user__id_number__icontains=search)
            )
            try:
                tn = int(search)
                q |= Q(table__table_number=tn)
            except ValueError:
                pass
            qs = qs.filter(q)
        ordering = self.request.query_params.get("ordering") or "-start_time"
        order_map = {
            "id": "id",
            "-id": "-id",
            "start_time": "start_time",
            "-start_time": "-start_time",
            "end_time": "end_time",
            "-end_time": "-end_time",
            "created_at": "created_at",
            "-created_at": "-created_at",
            "duration_minutes": "duration_minutes",
            "-duration_minutes": "-duration_minutes",
            "table_number": "table__table_number",
            "-table_number": "-table__table_number",
            "user_email": "user__email",
            "-user_email": "-user__email",
            "user_name": "user__name",
            "-user_name": "-user__name",
            "is_available": "is_available",
            "-is_available": "-is_available",
        }
        if ordering in order_map:
            qs = qs.order_by(order_map[ordering])
        else:
            qs = qs.order_by("-start_time")
        return qs


class AdminReservationDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AdminReservationSerializer
    queryset = Reservation.objects.select_related("user", "table").all()


class AdminWeightSensorListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AdminWeightSensorSerializer

    def get_queryset(self):
        return (
            WeightSensor.objects.prefetch_related(
                Prefetch(
                    "tables",
                    queryset=Table.objects.all().order_by("table_number"),
                )
            )
            .all()
            .order_by("id")
        )


class AdminWeightSensorDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AdminWeightSensorSerializer

    def get_queryset(self):
        return WeightSensor.objects.prefetch_related(
            Prefetch(
                "tables",
                queryset=Table.objects.all().order_by("table_number"),
            )
        ).all()


class AdminLCDDisplayListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AdminLCDDisplaySerializer

    def get_queryset(self):
        return LCDDisplay.objects.select_related("table").all().order_by("id")


class AdminLCDDisplayDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AdminLCDDisplaySerializer

    def get_queryset(self):
        return LCDDisplay.objects.select_related("table").all()


class AdminTableListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AdminTableSerializer

    def get_queryset(self):
        qs = (
            Table.objects.select_related("weight_sensor", "lcd_display")
            .all()
            .order_by("table_number")
        )
        floor = self.request.query_params.get("floor")
        if floor is not None:
            try:
                floor_int = int(floor)
            except (TypeError, ValueError):
                floor_int = None
            if floor_int is not None:
                qs = qs.filter(library_floor=floor_int)
        return qs


class AdminTableDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AdminTableSerializer
    queryset = Table.objects.select_related("weight_sensor", "lcd_display").all()


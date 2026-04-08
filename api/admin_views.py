from rest_framework import generics

from .models import Table
from .permissions import IsAdminRole
from .serializers import AdminTableSerializer


class AdminTableListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AdminTableSerializer

    def get_queryset(self):
        qs = Table.objects.all().order_by("table_number")
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
    queryset = Table.objects.all()


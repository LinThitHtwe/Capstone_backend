from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User
from .permissions import IsAdminRole
from .serializers import (
    CustomTokenObtainPairSerializer,
    SignupSerializer,
    UserMeSerializer,
)


class SignupView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = SignupSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            UserMeSerializer(serializer.instance).data,
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class AdminMeView(generics.RetrieveAPIView):
    """Example admin-only endpoint; extend `/api/admin/` with real dashboard APIs."""

    permission_classes = [IsAdminRole]
    serializer_class = UserMeSerializer
    queryset = User.objects.all()

    def get_object(self):
        return self.request.user

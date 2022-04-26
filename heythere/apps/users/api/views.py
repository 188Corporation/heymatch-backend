from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny

from .serializers import UserProfileSerializer

User = get_user_model()


class UserProfileViewSet(RetrieveAPIView):
    serializer_class = UserProfileSerializer
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]

    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, id=self.request.user.id)
        return obj

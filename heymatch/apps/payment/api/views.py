from typing import Any

from django.contrib.auth import get_user_model
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from heymatch.apps.payment.models import FreePassItem, PointItem

from .serializers import FreePassItemItemSerializer, PointItemSerializer

User = get_user_model()


class PaymentItemViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        pi_qs = PointItem.objects.all()
        fpi_qs = FreePassItem.objects.all()
        pi_serializer = PointItemSerializer(pi_qs, many=True)
        fpi_serializer = FreePassItemItemSerializer(fpi_qs, many=True)
        data = {
            "point_items": pi_serializer.data,
            "free_pass_items": fpi_serializer.data,
        }
        return Response(data, status.HTTP_200_OK)

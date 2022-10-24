import json
from itertools import chain
from typing import Any, Union

from django.conf import settings
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from heymatch.apps.payment.models import (
    FreePassItem,
    PlayStoreValidatedReceipt,
    PointItem,
    UserPurchase,
)
from heymatch.shared.exceptions import (
    ReceiptItemNotFound,
    ReceiptNotPurchasedException,
    ReceiptWrongEnvException,
)

from .serializers import (
    FreePassItemItemSerializer,
    PointItemSerializer,
    ReceiptValidationSerializer,
)

google_play_validator = settings.GOOGLE_PLAY_VALIDATOR
apple_store_validator = settings.APP_STORE_VALIDATOR


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


class ReceiptValidationViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=ReceiptValidationSerializer)
    def validate(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        asr = None
        psr = None
        platform = request.data["platform"]
        receipt = json.loads(request.data["receipt"])

        point_items = PointItem.objects.all()
        free_pass_items = FreePassItem.objects.all()
        all_items = list(chain(point_items, free_pass_items))

        # Validate receipt
        if platform == "android":
            validated_result = self.validate_android_receipt(receipt)
            psr = PlayStoreValidatedReceipt.objects.create(
                receipt=receipt, validated_result=validated_result
            )
            purchased_item = self.find_item(psr.productId, all_items)

        elif platform == "ios":
            # TODO
            return Response(data="API not ready", status=status.HTTP_400_BAD_REQUEST)

        # Process item
        self.process_purchase(purchased_item)

        # Save the result
        UserPurchase.objects.create(
            user=request.user,
            platform=platform,
            play_store_receipt=psr,
            apple_store_receipt=asr,
            purchase_processed=True,
        )
        return Response(status=status.HTTP_200_OK)

    @staticmethod
    def validate_android_receipt(receipt: dict):
        validated_result = dict(
            google_play_validator.verify_with_result(
                purchase_token=receipt["purchaseToken"],
                product_sku=receipt["productId"],
                is_subscription=False,
            ).raw_response
        )
        # if not purchased
        if receipt["purchaseState"] != 0:
            raise ReceiptNotPurchasedException()

        # if purchase is TEST mode but server is PROD mode.
        purchase_type = validated_result.get("purchaseType", None)
        if purchase_type in [0, 1, 2] and not settings.IS_INAPP_TESTING:
            # receipt is fake (internal testing) but server is prod mode. Deny.
            raise ReceiptWrongEnvException()
        return validated_result

    @staticmethod
    def find_item(product_id: str, all_items: list):
        # Process purchase
        for item in all_items:
            if item.product_id == product_id:
                return item
        raise ReceiptItemNotFound()

    def process_purchase(self, purchased_item: Union[PointItem, FreePassItem]):
        user = self.request.user

        if type(purchased_item) is PointItem:
            user.point_balance = (
                user.point_balance
                + purchased_item.default_point
                + purchased_item.bonus_point
            )

        elif type(purchased_item) is FreePassItem:
            user.free_pass = True
            user.free_pass_active_until = timezone.now() + timezone.timedelta(
                hours=purchased_item.free_pass_duration_in_hour
            )
        user.save()

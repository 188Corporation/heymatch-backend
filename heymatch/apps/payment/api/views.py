import json
import logging
from itertools import chain
from typing import Any, Union

from django.conf import settings
from django.db import IntegrityError
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from inapppy import InAppPyValidationError
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from heymatch.apps.payment.models import (
    AppleStoreValidatedReceipt,
    FreePassItem,
    PlayStoreValidatedReceipt,
    PointItem,
    UserPurchase,
)
from heymatch.shared.exceptions import (
    ReceiptAlreadyProcessedException,
    ReceiptInvalidPlatformRequestException,
    ReceiptItemNotFound,
    ReceiptNotPurchasedException,
    ReceiptProcessFailedException,
    ReceiptWrongEnvException,
)
from heymatch.shared.permissions import IsUserActive

from .serializers import (
    FreePassItemItemSerializer,
    PointItemSerializer,
    ReceiptValidationSerializer,
    UserPurchaseSerializer,
)

google_play_validator = settings.GOOGLE_PLAY_VALIDATOR
apple_store_validator = settings.APP_STORE_VALIDATOR
logger = logging.getLogger(__name__)


class PaymentItemViewSet(viewsets.ViewSet):
    permission_classes = [
        IsAuthenticated,
        IsUserActive,
    ]

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
    permission_classes = [IsAuthenticated, IsUserActive]

    @swagger_auto_schema(request_body=ReceiptValidationSerializer)
    def validate(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        platform = request.data["platform"]
        receipt_str = request.data["receipt"]

        point_items = PointItem.objects.all()
        free_pass_items = FreePassItem.objects.all()
        all_items = list(chain(point_items, free_pass_items))

        # Validate receipt
        try:
            if platform == UserPurchase.PlatformChoices.ANDROID:
                receipt = json.loads(receipt_str)
                validated_result = self.validate_android_receipt(receipt=receipt)
                try:
                    validated_receipt = PlayStoreValidatedReceipt.objects.create(
                        receipt=receipt, validated_result=validated_result
                    )
                except IntegrityError as e:
                    logger.error(e, exc_info=True)
                    raise ReceiptAlreadyProcessedException()
                purchased_item = self.find_item(validated_receipt.productId, all_items)
            elif platform == UserPurchase.PlatformChoices.IOS:
                validated_result = self.validate_ios_receipt(receipt=receipt_str)
                try:
                    validated_receipt = AppleStoreValidatedReceipt.objects.create(
                        validated_result=validated_result
                    )
                except IntegrityError as e:
                    logger.error(e, exc_info=True)
                    raise ReceiptAlreadyProcessedException()
                purchased_item = self.find_item(validated_receipt.product_id, all_items)
            else:
                raise ReceiptInvalidPlatformRequestException()

            # Process item
            up: UserPurchase = self.process_purchase(
                platform=platform,
                receipt=validated_receipt,
                purchased_item=purchased_item,
            )
        # Since payment is critical, catch all exceptions
        except Exception as e:
            logger.error(e, exc_info=True)
            return Response(
                data="알 수 없는 문제가 생겼어요..😵‍💫",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Serialize and return
        serializer = UserPurchaseSerializer(instance=up)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

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
    def validate_ios_receipt(receipt: str):
        try:
            validated_result = dict(
                apple_store_validator.validate(
                    receipt=receipt,
                    exclude_old_transactions=False,
                )
            )
        except InAppPyValidationError as ex:
            raise ReceiptProcessFailedException(
                detail=ReceiptProcessFailedException.detail + str(ex.raw_response)
            )

        # if not purchased
        if (
            validated_result["receipt"]["in_app"][0]["in_app_ownership_type"]
            != "PURCHASED"
        ):
            raise ReceiptNotPurchasedException()

        # # if purchase is SANDBOX mode but server is PROD mode.
        if (
            validated_result["environment"] != "Sandbox"
            and not settings.IS_INAPP_TESTING
        ):
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

    def process_purchase(
        self,
        platform: str,
        receipt: Union[PlayStoreValidatedReceipt, AppleStoreValidatedReceipt],
        purchased_item: Union[PointItem, FreePassItem],
    ) -> UserPurchase:
        user = self.request.user
        point_item = None
        free_pass_item = None

        if type(purchased_item) is PointItem:
            user.point_balance = (
                user.point_balance
                + purchased_item.default_point
                + purchased_item.bonus_point
            )
            point_item = purchased_item

        elif type(purchased_item) is FreePassItem:
            user.free_pass = True
            user.free_pass_active_until = timezone.now() + timezone.timedelta(
                hours=purchased_item.free_pass_duration_in_hour
            )
            free_pass_item = purchased_item
        user.save()

        psr = receipt if type(receipt) is PlayStoreValidatedReceipt else None
        asr = receipt if type(receipt) is AppleStoreValidatedReceipt else None

        up = UserPurchase.objects.create(
            user=user,
            platform=platform,
            play_store_receipt=psr,
            apple_store_receipt=asr,
            purchase_processed=True,
            point_item=point_item,
            free_pass_item=free_pass_item,
        )
        return up

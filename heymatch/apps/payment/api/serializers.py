from rest_framework import serializers

from heymatch.apps.payment.models import (
    AppleStoreValidatedReceipt,
    FreePassItem,
    PlayStoreValidatedReceipt,
    PointItem,
    UserPurchase,
)


class PointItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PointItem
        fields = "__all__"


class FreePassItemItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FreePassItem
        fields = "__all__"


class ReceiptValidationSerializer(serializers.Serializer):
    platform = serializers.CharField(required=True, max_length=20)
    receipt = serializers.CharField(required=True)


class PlayStoreReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayStoreValidatedReceipt
        fields = "__all__"


class AppleStoreReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppleStoreValidatedReceipt
        fields = "__all__"


class UserPurchaseSerializer(serializers.ModelSerializer):
    apple_store_receipt = AppleStoreReceiptSerializer(read_only=True)
    play_store_receipt = PlayStoreReceiptSerializer(read_only=True)
    point_item = PointItemSerializer(read_only=True)
    free_pass = FreePassItemItemSerializer(read_only=True)

    class Meta:
        model = UserPurchase
        fields = "__all__"

from rest_framework import serializers

from heymatch.apps.payment.models import FreePassItem, PointItem


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

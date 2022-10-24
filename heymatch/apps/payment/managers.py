from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class PlayStoreValidatedReceiptManager(models.Manager):
    def create(self, receipt: dict, validated_result: dict):
        """
        Delete redundant fields from receipt and save

        1) Android Receipt example
            {
                "orderId": "GPA.3383-2526-5819-26341",
                "packageName": "com.co188.heythere",
                "productId": "com.co188.heymatch.point_item2",
                "purchaseTime": 1666510061922,
                "purchaseState": 0,
                "purchaseToken": "ogepbbmmdiogdgoimealggcf.AO-J1OxLQmZiQRBqYZvyZP...",
                "quantity": 1,
                "acknowledged": false,
            }

        2) Verified Result
            {
                "purchaseTimeMillis": "1666510061922",
                "purchaseState": 0,
                "consumptionState": 1,
                "developerPayload": "",
                "orderId": "GPA.3383-2526-5819-26341",
                "purchaseType": 0,
                "acknowledgementState": 1,
                "kind": "androidpublisher#productPurchase",
                "regionCode": "KR",
            }

        - Explanation
            - purchaseState: 0. Purchased 1. Canceled 2. Pending
            - consumptionState: 0. Yet to be consumed 1. Consumed
            - purchaseType: This field is only set if this purchase was not made using the standard
                in-app billing flow. Possible values are: 0. Test (i.e. purchased from a license testing account)
                1. Promo (i.e. purchased using a promo code)
                2. Rewarded (i.e. from watching a video ad instead of paying)
        """
        del receipt["purchaseTime"]
        del receipt["purchaseState"]
        del receipt["quantity"]
        del receipt["acknowledged"]

        validated_receipt = self.model({**receipt, **validated_result})
        validated_receipt.save(using=self._db)
        return validated_receipt

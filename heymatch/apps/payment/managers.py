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

        2) Verified Result example
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
              in-app billing flow. Possible values are:
                0. Test (i.e. purchased from a license testing account)
                1. Promo (i.e. purchased using a promo code)
                2. Rewarded (i.e. from watching a video ad instead of paying)
        """
        del receipt["purchaseTime"]
        del receipt["purchaseState"]
        del receipt["acknowledged"]
        del validated_result["developerPayload"]

        validated_receipt = self.model(**{**receipt, **validated_result})
        validated_receipt.save(using=self._db)
        return validated_receipt


class AppleStoreValidatedReceiptManager(models.Manager):
    """
        Apple validated result is the only thing you need to know. Original receipt string
        received from client is encrypted.

        1) Verified Result example
        {
        "receipt": {
            "receipt_type": "ProductionSandbox",
            "adam_id": 0,
            "app_item_id": 0,
            "bundle_id": "com.co188.heythere",
            "application_version": "11",
            "download_id": 0,
            "version_external_identifier": 0,
            "receipt_creation_date": "2022-10-31 15:32:55 Etc/GMT",
            "receipt_creation_date_ms": "1667230375000",
            "receipt_creation_date_pst": "2022-10-31 08:32:55 America/Los_Angeles",
            "request_date": "2022-11-01 11:13:28 Etc/GMT",
            "request_date_ms": "1667301208380",
            "request_date_pst": "2022-11-01 04:13:28 America/Los_Angeles",
            "original_purchase_date": "2013-08-01 07:00:00 Etc/GMT",
            "original_purchase_date_ms": "1375340400000",
            "original_purchase_date_pst": "2013-08-01 00:00:00 America/Los_Angeles",
            "original_application_version": "1.0",
            "in_app": [
                {
                    "quantity": "1",
                    "product_id": "com.co188.heymatch.point_item1",
                    "transaction_id": "2000000190274505",
                    "original_transaction_id": "2000000190274505",
                    "purchase_date": "2022-10-31 15:32:55 Etc/GMT",
                    "purchase_date_ms": "1667230375000",
                    "purchase_date_pst": "2022-10-31 08:32:55 America/Los_Angeles",
                    "original_purchase_date": "2022-10-31 15:32:55 Etc/GMT",
                    "original_purchase_date_ms": "1667230375000",
                    "original_purchase_date_pst": "2022-10-31 08:32:55 America/Los_Angeles",
                    "is_trial_period": "false",
                    "in_app_ownership_type": "PURCHASED",
                }
            ],
        },
        "environment": "Sandbox",
        "status": 0,
    }
    """

    def create(self, validated_result: dict):
        receipt_data = validated_result["receipt"]
        in_app_data = receipt_data["in_app"][0]
        processed_result = {
            "product_id": in_app_data["product_id"],
            "transaction_id": in_app_data["transaction_id"],
            "original_transaction_id": in_app_data["original_transaction_id"],
            "quantity": in_app_data["quantity"],
            "status": validated_result["status"],
            "receipt_creation_date_ms": receipt_data["receipt_creation_date_ms"],
            "request_date_ms": receipt_data["request_date_ms"],
            "purchase_date_ms": in_app_data["purchase_date_ms"],
            "original_purchase_date_ms": in_app_data["original_purchase_date_ms"],
            "is_trial_period": bool(in_app_data["is_trial_period"]),
            "in_app_ownership_type": in_app_data["in_app_ownership_type"],
            "environment": validated_result["environment"],
        }
        validated_receipt = self.model(**processed_result)
        validated_receipt.save(using=self._db)
        return validated_receipt

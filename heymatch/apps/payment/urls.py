from django.urls import path

from .api.views import PaymentItemViewSet, ReceiptValidationViewSet

app_name = "payment"

payment_item_list_view = PaymentItemViewSet.as_view({"get": "list"})
receipt_validate_post_view = ReceiptValidationViewSet.as_view({"post": "validate"})

urlpatterns = [
    path("items/", payment_item_list_view, name="payment-items-list"),
    path("receipt/", receipt_validate_post_view, name="payment-receipt"),
]

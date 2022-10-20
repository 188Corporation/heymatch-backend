from django.urls import path

from .api.views import PaymentItemViewSet

app_name = "payment"

payment_item_list_view = PaymentItemViewSet.as_view({"get": "list"})

urlpatterns = [
    path("items/", payment_item_list_view, name="payment-items-list"),
]

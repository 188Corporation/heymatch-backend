from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import MatchRequest


@admin.register(MatchRequest)
class MatchRequestAdmin(SimpleHistoryAdmin):
    list_display = [
        "id",
        "sender_group",
        "receiver_group",
        "status",
        "created_at",
        "is_active",
    ]
    history_list_display = ["status", *list_display]
    search_fields = [
        "id",
        "sender_group",
        "receiver_group",
        "status",
        "created_at",
        "is_active",
    ]

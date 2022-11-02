from django.contrib import admin

from .models import MatchRequest


@admin.register(MatchRequest)
class MatchRequestAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "sender_group",
        "receiver_group",
        "status",
        "created_at",
    ]
    search_fields = [
        "id",
        "sender_group",
        "receiver_group",
        "status",
        "created_at",
    ]

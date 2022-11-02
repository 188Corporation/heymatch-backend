from django.contrib import admin

from .models import MatchRequest


@admin.register(MatchRequest)
class MatchRequestAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "uuid",
        "sender_group",
        "receiver_group",
        "status",
    ]
    search_fields = [
        "id",
        "uuid",
        "sender_group",
        "receiver_group",
        "status",
    ]

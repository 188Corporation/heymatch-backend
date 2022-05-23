from django.contrib import admin

from .models import MatchRequest


@admin.register(MatchRequest)
class MatchRequestAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "uuid",
        "sender",
        "receiver",
        "title",
        "content",
        "unread",
        "accepted",
    ]
    search_fields = [
        "id",
        "uuid",
        "sender",
        "receiver",
        "title",
        "content",
        "unread",
        "accepted",
    ]

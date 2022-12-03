from django.contrib import admin

from .models import StreamChannel


@admin.register(StreamChannel)
class StreamChannelAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "cid",
        "participants",
        "created_at",
    ]
    search_fields = [
        "id",
        "cid",
        "participants",
        "created_at",
    ]

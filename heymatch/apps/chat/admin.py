from django.contrib import admin

from .models import StreamChannel


@admin.register(StreamChannel)
class StreamChannelAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "stream_id",
        "cid",
        "type",
        "group_member",
        "is_active",
        "created_at",
    ]
    search_fields = [
        "id",
        "stream_id",
        "cid",
        "type",
        "group_member",
        "is_active",
        "created_at",
    ]

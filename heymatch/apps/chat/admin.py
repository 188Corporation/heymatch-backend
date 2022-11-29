from django.contrib import admin

from .models import StreamChannel


@admin.register(StreamChannel)
class StreamChannelAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "cid",
        "joined_groups",
    ]
    search_fields = [
        "id",
        "cid",
        "joined_groups",
    ]

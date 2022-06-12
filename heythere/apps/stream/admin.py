from django.contrib import admin

from .models import StreamChatChannel, StreamChatChannelMember


@admin.register(StreamChatChannel)
class StreamChatChannelAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "type",
        "is_active",
    ]
    search_fields = [
        "id",
        "type",
        "is_active",
    ]


@admin.register(StreamChatChannelMember)
class StreamChatChannelMemberAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "member",
        "channel",
    ]
    search_fields = [
        "id",
        "member",
        "channel",
    ]

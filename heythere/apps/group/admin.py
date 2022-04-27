from django.contrib import admin

from .models import Group


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "title",
        "is_active",
    ]
    search_fields = [
        "id",
        "title",
        "is_active",
    ]

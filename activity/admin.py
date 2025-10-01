from django.contrib import admin

from .models import LoginEvent


@admin.register(LoginEvent)
class LoginEventAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "user", "username", "action", "ip_address")
    list_filter = ("action", "timestamp")
    search_fields = ("user__username", "username", "ip_address", "user_agent")
    readonly_fields = ("timestamp", "user", "username", "action", "ip_address", "user_agent", "path")
    ordering = ("-timestamp",)

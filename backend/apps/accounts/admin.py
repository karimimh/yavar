from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.accounts.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("phone",)
    list_display = ("phone", "preferred_name", "is_staff", "is_operator", "is_suspended")
    search_fields = ("phone", "preferred_name")
    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        ("Profile", {"fields": ("preferred_name", "timezone", "sms_opt_in")}),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_operator", "is_superuser", "is_suspended", "groups")},
        ),
    )
    add_fieldsets = ((None, {"fields": ("phone", "password1", "password2")}),)
    filter_horizontal = ("groups", "user_permissions")

from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, EmailVerificationToken, PasswordResetOTP


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'display_name', 'is_verified', 'is_active', 'is_staff', 'created_at')
    list_filter = ('is_verified', 'is_active', 'is_staff')
    search_fields = ('email', 'display_name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('display_name',)}),
        ('Status', {'fields': ('is_verified', 'is_active', 'is_staff', 'is_superuser')}),
        ('Permissions', {'fields': ('groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'display_name', 'password1', 'password2'),
        }),
    )


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_used', 'created_at', 'expires_at')
    list_filter = ('is_used',)
    search_fields = ('user__email',)
    readonly_fields = ('token', 'created_at')


@admin.register(PasswordResetOTP)
class PasswordResetOTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_used', 'created_at', 'expires_at')
    list_filter = ('is_used',)
    search_fields = ('user__email',)
    readonly_fields = ('otp', 'created_at')
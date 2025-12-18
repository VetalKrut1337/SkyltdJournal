from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from ..models import JournalRecord, Service, Vehicle, Client


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # Настройка отображения полей в списке пользователей
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'position',  # Ваше кастомное поле
        'is_staff'
    )

    # Настройка фильтров справа
    list_filter = ('position', 'is_staff', 'is_superuser', 'groups')

    # Секции полей при РЕДАКТИРОВАНИИ пользователя
    # Мы берем стандартные секции UserAdmin и добавляем свою
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {'fields': ('position',)}),
    )

    # Секции полей при СОЗДАНИИ пользователя
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Дополнительная информация', {'fields': ('position',)}),
    )


# -----------------------------
# Client
# -----------------------------
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone')
    search_fields = ('name', 'phone')
    ordering = ('name',)

# -----------------------------
# Vehicle
# -----------------------------
@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('brand', 'model', 'plate_number', 'client')
    search_fields = ('brand', 'model', 'plate_number', 'client__name')
    list_filter = ('brand',)
    autocomplete_fields = ('client',)

# -----------------------------
# Service
# -----------------------------
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)

# -----------------------------
# JournalRecord
# -----------------------------
@admin.register(JournalRecord)
class JournalRecordAdmin(admin.ModelAdmin):
    list_display = ('date', 'department', 'client', 'vehicle', 'service', 'comment')
    list_filter = ('department', 'date', 'service')
    search_fields = ('client__name', 'vehicle__plate_number', 'comment')
    autocomplete_fields = ('client', 'vehicle', 'service', 'services')
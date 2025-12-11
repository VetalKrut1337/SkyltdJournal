from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


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
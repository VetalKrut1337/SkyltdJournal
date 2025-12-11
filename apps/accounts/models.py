from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Користувач без ролей. Доступ визначається permissions.
    """
    # Добавляем должность
    position = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Посада"
    )

    class Meta:
        verbose_name = "Користувач"
        verbose_name_plural = "Користувачі"

    def __str__(self):
        # Красивое отображение в админке: Имя Фамилия (Должность)
        full_name = f"{self.first_name} {self.last_name}".strip()
        if not full_name:
            return self.username
        if self.position:
            return f"{full_name} ({self.position})"
        return full_name
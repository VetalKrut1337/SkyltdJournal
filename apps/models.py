from django.core.exceptions import ValidationError
from django.db import models

from SkyltdJournal import settings


class Client(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True, db_index=True)

    def __str__(self):
        return f"{self.name} ({self.phone})" if self.phone else self.name

    class Meta:
        ordering = ["name"]
        verbose_name = "Клієнт"
        verbose_name_plural = "Клієнти"


class Vehicle(models.Model):
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    plate_number = models.CharField(max_length=20)

    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vehicles"
    )

    def __str__(self):
        return f"{self.brand} {self.model} — {self.plate_number}"

    class Meta:
        ordering = ["brand", "model"]
        verbose_name = "Автомобіль"
        verbose_name_plural = "Автомобілі"
        constraints = [
            models.UniqueConstraint(
                fields=["plate_number", "brand", "model", "client"],
                name="unique_vehicle_per_client"
            )
        ]


class Service(models.Model):
    name = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        verbose_name = "Послуга"
        verbose_name_plural = "Послуги"


class JournalRecord(models.Model):

    DEPARTMENT_CHOICES = (
        ("sales", "Відділ продажів"),
        ("service", "Відділ сервісу"),
    )

    date = models.DateTimeField(
        verbose_name="Дата та час",
        auto_now_add=True
    )

    is_priority = models.BooleanField(
        default=False,
        verbose_name="Пріоритет"
    )

    department = models.CharField(
        max_length=20,
        choices=DEPARTMENT_CHOICES,
        db_index=True
    )

    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="journal_records"
    )

    phone = models.CharField(max_length=20, blank=True, null=True)

    # For service dept
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="journal_records"
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="journal_records"
    )
    services = models.ManyToManyField(
        Service,
        blank=True,
        related_name="journal_records_many"
    )

    comment = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.get_department_display()} — {self.date}"

    class Meta:
        ordering = ["-is_priority", "-date"]
        verbose_name = "Запис журналу"
        verbose_name_plural = "Записи журналу"


# models.py

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('in_progress', 'В работе'),
        ('done', 'Готово'),
        ('canceled', 'Отменено'),
        ('partially_done', 'Частично выполнено'),
    ]

    # Сотрудники (many-to-many вместо user + user2)
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='appointments_managed',
        verbose_name="Сотрудники",
        blank=True,  # временно, пока мигрируем данные
    )

    vehicle = models.ForeignKey(
        'Vehicle',
        on_delete=models.PROTECT,
        related_name='appointments'
    )

    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appointments"
    )

    services = models.ManyToManyField(
        'Service',
        related_name='appointments',
        blank=True,
        verbose_name="Послуги"
    )

    start_time = models.DateTimeField(verbose_name="Початок")
    duration_minutes = models.PositiveIntegerField(
        verbose_name="Тривалість, хв",
        help_text="Тривалість візиту у хвилинах"
    )

    description = models.TextField(blank=True, verbose_name="Описание работ")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Статус"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    class Meta:
        verbose_name = "Запис на сервіс"
        verbose_name_plural = "Записи на сервіс"
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.vehicle} ({self.start_time.strftime('%d.%m %H:%M')})"

    @property
    def end_time(self):
        from datetime import timedelta
        if not self.start_time or not self.duration_minutes:
            return None
        return self.start_time + timedelta(minutes=self.duration_minutes)

    @property
    def users_display(self):
        """Имена сотрудников через запятую."""
        names = []
        for u in self.users.all():
            full = f"{u.first_name} {u.last_name}".strip()
            names.append(full or u.username)
        return ", ".join(names) if names else "—"

    def clean(self):
        if self.duration_minutes and self.duration_minutes <= 0:
            raise ValidationError("Длительность должна быть больше 0 минут.")

    def overlaps_with(self, other: "Appointment") -> bool:
        if not self.start_time or not self.end_time or not other.start_time or not other.end_time:
            return False
        return self.start_time < other.end_time and self.end_time > other.start_time

from django.db import models


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
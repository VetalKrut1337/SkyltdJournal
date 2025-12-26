from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# Форматируем дату и время для дополнения (локальное время)
from django.utils import timezone
import pytz

from apps.models import Client, Vehicle, Service, JournalRecord
from apps.accounts.models import User
from .serializers import (
    ClientSerializer, VehicleSerializer,
    ServiceSerializer, JournalRecordSerializer, UserSerializer
)


class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all().prefetch_related('vehicles')
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """Переопределяем create для обработки привязки машин"""
        data = request.data.copy()
        
        # Получаем vehicle_ids из данных (может быть список)
        vehicle_ids = data.pop('vehicle_ids', [])
        if isinstance(vehicle_ids, str):
            # Если пришла строка, пытаемся распарсить как JSON
            import json
            try:
                vehicle_ids = json.loads(vehicle_ids)
            except:
                vehicle_ids = [vehicle_ids] if vehicle_ids else []
        elif not isinstance(vehicle_ids, list):
            vehicle_ids = []
        
        # Преобразуем в числа
        vehicle_ids = [int(vid) for vid in vehicle_ids if vid]
        
        # Создаем клиента
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        client = serializer.save()
        
        # Привязываем машины к клиенту
        if vehicle_ids:
            Vehicle.objects.filter(id__in=vehicle_ids).update(client=client)
        
        # Возвращаем клиента с обновленными данными
        return Response(ClientSerializer(client).data, status=201)

    @extend_schema(
        summary="Автопошук клієнта за ім'ям (з можливим створенням)",
        parameters=[
            OpenApiParameter(name="q", type=str, required=True),
            OpenApiParameter(name="phone", type=str, required=False),
        ]
    )
    @action(detail=False, methods=['get'], url_path='find-by-name')
    def find_by_name(self, request):
        q = request.query_params.get("q", "").strip()
        phone = request.query_params.get("phone", "").strip()

        if not q:
            raise ValidationError({"error": "Потрібно передати параметр ?q="})

        clients = Client.objects.filter(name__icontains=q)

        # Если нашли несколько
        if clients.count() > 1:
            return Response({
                "exists": True,
                "multiple": True,
                "results": ClientSerializer(clients, many=True).data
            })

        # Если нашли одного
        if clients.count() == 1:
            return Response({
                "exists": True,
                "multiple": False,
                "client": ClientSerializer(clients.first()).data
            })

        # ---- НЕ НАЙДЕНО → пробуем создать ----
        if not phone:
            raise ValidationError({
                "error": "Клієнта не знайдено. Для створення потрібно передати ?phone="
            })

        client = Client.objects.create(name=q, phone=phone)

        return Response({
            "exists": False,
            "created": True,
            "client": ClientSerializer(client).data
        })

    @extend_schema(
        summary="Автопошук клієнта за телефоном (з можливим створенням)",
        parameters=[
            OpenApiParameter(name="q", type=str, required=True),
            OpenApiParameter(name="name", type=str, required=False),
        ]
    )
    @action(detail=False, methods=['get'], url_path='find-by-phone')
    def find_by_phone(self, request):
        q = request.query_params.get("q", "").strip()
        name = request.query_params.get("name", "").strip()

        if not q:
            raise ValidationError({"error": "Потрібно передати параметр ?q="})

        clients = Client.objects.filter(phone__icontains=q)

        if clients.count() > 1:
            return Response({
                "exists": True,
                "multiple": True,
                "results": ClientSerializer(clients, many=True).data
            })

        if clients.count() == 1:
            return Response({
                "exists": True,
                "multiple": False,
                "client": ClientSerializer(clients.first()).data
            })

        # ---- НЕ НАЙДЕНО → создание ----
        if not name:
            raise ValidationError({
                "error": "Клієнта не знайдено. Для створення потрібно передати ?name="
            })

        client = Client.objects.create(name=name, phone=q)

        return Response({
            "exists": False,
            "created": True,
            "client": ClientSerializer(client).data
        })



class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all().select_related('client')
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Отримати машини без власника",
        responses=VehicleSerializer(many=True),
    )
    @action(detail=False, methods=["GET"])
    def free(self, request):
        """Возвращает список машин без владельца"""
        free_vehicles = Vehicle.objects.filter(client__isnull=True)
        return Response(VehicleSerializer(free_vehicles, many=True).data)

    # ============================================================
    # 1) АВТОПОИСК ПО НОМЕРУ
    # ============================================================
    @extend_schema(
        summary="Автопошук авто за номером",
        parameters=[
            OpenApiParameter(
                name="plate_number",
                type=str,
                required=True,
                location=OpenApiParameter.QUERY,
                description="Номер автомобіля (повний або частковий)"
            )
        ],
        responses=VehicleSerializer(many=True),
    )
    @action(detail=False, methods=["GET"])
    def auto_find_by_number(self, request):
        number = request.query_params.get('plate_number')
        if not number:
            return Response({"error": "Параметр plate_number є обов'язковим"}, status=400)

        vehicles = Vehicle.objects.filter(plate_number__icontains=number)

        return Response({
            "count": vehicles.count(),
            "results": VehicleSerializer(vehicles, many=True).data
        })

    # ============================================================
    # 2) АВТОПОИСК ПО БРЕНДУ
    # ============================================================
    @extend_schema(
        summary="Автопошук авто за брендом",
        parameters=[
            OpenApiParameter(
                name="brand",
                type=str,
                required=True,
                location=OpenApiParameter.QUERY,
                description="Бренд авто"
            )
        ],
        responses=VehicleSerializer(many=True),
    )
    @action(detail=False, methods=["GET"])
    def auto_find_by_brand(self, request):
        brand = request.query_params.get('brand')
        if not brand:
            return Response({"error": "Параметр brand є обов'язковим"}, status=400)

        vehicles = Vehicle.objects.filter(brand__icontains=brand)

        return Response({
            "count": vehicles.count(),
            "results": VehicleSerializer(vehicles, many=True).data
        })

    # ============================================================
    # 3) АВТОПОИСК ПО МОДЕЛИ
    # ============================================================
    @extend_schema(
        summary="Автопошук авто за моделлю",
        parameters=[
            OpenApiParameter(
                name="model",
                type=str,
                required=True,
                location=OpenApiParameter.QUERY,
                description="Модель авто"
            )
        ],
        responses=VehicleSerializer(many=True),
    )
    @action(detail=False, methods=["GET"])
    def auto_find_by_model(self, request):
        model = request.query_params.get('model')
        if not model:
            return Response({"error": "Параметр model є обов'язковим"}, status=400)

        vehicles = Vehicle.objects.filter(model__icontains=model)

        return Response({
            "count": vehicles.count(),
            "results": VehicleSerializer(vehicles, many=True).data
        })

    # ============================================================
    # 4) ПЕРЕОПРЕДЕЛЕННЫЙ create()
    # ============================================================
    @extend_schema(
        summary="Створення авто (з автоперевіркою існування)",
        description=(
            "Якщо авто з таким номером вже існує — повертається існуючий запис.\n"
            "Якщо авто не існує — необхідно вказати brand та model."
        ),
        request=VehicleSerializer,
        responses=VehicleSerializer,
    )
    def create(self, request, *args, **kwargs):
        data = request.data.copy()

        plate = data.get("plate_number", "").strip()
        brand = data.get("brand", "").strip()
        model = data.get("model", "").strip()

        # --- проверка на обязательные поля
        if not brand or not model:
            return Response(
                {"error": "Для створення нового авто необхідно вказати brand та model"},
                status=400
            )

        # --- валидация: проверяем, существует ли машина с такими же номером, брендом и моделью одновременно
        existing_vehicle = Vehicle.objects.filter(
            plate_number__iexact=plate,
            brand__iexact=brand,
            model__iexact=model
        ).first()

        if existing_vehicle:
            return Response(
                {"error": "Машина з такими номером, брендом та моделлю вже існує"},
                status=400
            )

        return super().create(request, *args, **kwargs)


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]


class JournalRecordViewSet(viewsets.ModelViewSet):
    queryset = JournalRecord.objects.all()
    serializer_class = JournalRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_header(self):
        local_tz = pytz.timezone('Europe/Kiev')
        now = timezone.now()
        if timezone.is_aware(now):
            local_now = now.astimezone(local_tz)
        else:
            local_now = local_tz.localize(now)

        username = self.request.user.username
        date_str = local_now.strftime("%d.%m.%Y %H:%M")
        header = f"[ADD][{username}][{date_str}]"
        return header

    # ------------------------------------
    # ФИЛЬТРАЦИЯ ДЛЯ /journal/?department=
    # ------------------------------------
    def get_queryset(self):
        qs = super().get_queryset()
        department = self.request.query_params.get("department")

        if department in ["sales", "service"]:
            qs = qs.filter(department=department)

        return qs.order_by("-date")

    # ---------------------------------------------------
    # SWAGGER: добавить department в список параметров
    # ---------------------------------------------------
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="department",
                type=str,
                description="Фільтрація по відділу: sales або service",
                required=False
            )
        ]
    )
    def list(self, *args, **kwargs):
        return super().list(*args, **kwargs)

    # ---------------------------------------------------
    # ПЕРЕОПРЕДЕЛЁННЫЙ create() С ТВОЕЙ ЛОГИКОЙ
    # ---------------------------------------------------
    @extend_schema(
        summary="Створення запису журналу з автопошуком",
        description="Автоматичний пошук/створення клієнта та авто при створенні запису."
    )
    def create(self, request, *args, **kwargs):
        # Берём данные из запиту і акуратно працюємо з допоміжними полями
        data = request.data.copy()

        client = None
        vehicle = None

        # Явно переданий клієнт / авто з фронтенду
        client_id = data.get("client_id")
        vehicle_id = data.get("vehicle_id")

        name = data.pop("client_name", None)
        phone = data.get("phone")
        plate_number = data.pop("plate_number", None)

        # ---------------------------
        # 1. Якщо client_id переданий — використовуємо його
        # ---------------------------
        if client_id:
            try:
                client = Client.objects.get(id=client_id)
                data["client_id"] = client.id
                if not phone and client.phone:
                    data["phone"] = client.phone
            except Client.DoesNotExist:
                client = None

        # ---------------------------
        # 2. Автопошук клієнта (якщо client_id не знайшли)
        # ---------------------------
        if not client and (name or phone):
            qs = Client.objects.all()
            if name:
                qs = qs.filter(name__icontains=name)
            if phone:
                qs = qs.filter(phone__icontains=phone)

            if qs.count() == 1:
                client = qs.first()
                data["client_id"] = client.id
                if not phone and client.phone:
                    data["phone"] = client.phone

        # ---------------------------
        # 3. Якщо vehicle_id переданий — використовуємо його
        # ---------------------------
        if vehicle_id:
            try:
                vehicle = Vehicle.objects.select_related("client").get(id=vehicle_id)
                data["vehicle_id"] = vehicle.id

                # якщо клієнт не вказаний, беремо з авто
                if not client and vehicle.client:
                    client = vehicle.client
                    data["client_id"] = client.id
                    if not data.get("phone") and client.phone:
                        data["phone"] = client.phone
            except Vehicle.DoesNotExist:
                vehicle = None

        # ---------------------------
        # 4. Автопошук машини по номеру (якщо vehicle не знайшли)
        # ---------------------------
        if not vehicle and plate_number:
            vqs = Vehicle.objects.filter(plate_number__icontains=plate_number)

            if vqs.count() == 1:
                vehicle = vqs.first()
                data["vehicle_id"] = vehicle.id

                # если не указан клиент → берём из машины
                if not client and vehicle.client:
                    client = vehicle.client
                    data["client_id"] = client.id
                    if not data.get("phone") and client.phone:
                        data["phone"] = client.phone

        # ---------------------------
        # 5. Создание нового клиента (якщо так і не знайшли)
        # ---------------------------
        if not client and (name or phone):
            if not name or not phone:
                return Response(
                    {"error": "Для створення нового клієнта потрібно і name, і phone"},
                    status=400
                )
            client = Client.objects.create(name=name, phone=phone)
            data["client_id"] = client.id

        # ---------------------------
        # 6. Создание новой машины (якщо так і не знайшли)
        # ---------------------------
        brand = data.pop("brand", None)
        model = data.pop("model", None)
        plate_number = data.pop("plate_number", '-')
        department = data.get("department")

        if not vehicle and department=='service':
            if not brand or not model:
                return Response(
                    {"error": "Для створення нового авто потрібно brand і model"},
                    status=400
                )
            vehicle = Vehicle.objects.create(
                plate_number=plate_number,
                brand=brand,
                model=model,
                client=client
            )
            data["vehicle_id"] = vehicle.id

        # ---------------------------
        # 7. Обработка множественных сервисов
        # ---------------------------
        service_ids = data.pop("service_ids", [])
        if isinstance(service_ids, str):
            import json
            try:
                service_ids = json.loads(service_ids)
            except:
                service_ids = [service_ids] if service_ids else []
        elif not isinstance(service_ids, list):
            service_ids = []
        
        # Преобразуем в числа и фильтруем валидные
        service_ids = [int(sid) for sid in service_ids if sid]

        # ---------------------------
        # 7.5 Добавление header к комментарию при создании
        # ---------------------------
        comment = data.get("comment", "").strip()
        if comment:
            header = self.get_header()

            data["comment"] = f"{header}\n{comment}"

        # ---------------------------
        # 8. Создание записи журнала
        # ---------------------------
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        journal_record = serializer.save()

        # Привязываем множественные сервисы
        if service_ids:
            services = Service.objects.filter(id__in=service_ids, is_active=True)
            journal_record.services.set(services)

        return Response(self.get_serializer(journal_record).data, status=201)

    # ---------------------------------------------------
    # ПЕРЕОПРЕДЕЛЁННЫЙ update() ДЛЯ ДОПОЛНЕНИЯ КОММЕНТАРИЯ
    # ---------------------------------------------------
    @extend_schema(
        summary="Доповнення коментаря до запису журналу",
        description="Додає новий коментар до існуючого з датою та часом. Старий коментар не можна редагувати або видаляти."
    )
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data.copy()

        # Разрешаем обновлять только комментарий
        new_comment = data.get("comment", "").strip()

        if not new_comment:
            return Response(
                {"error": "Коментар не може бути порожнім"},
                status=400
            )

        header = self.get_header()


        # Если комментарий уже существует, добавляем новое дополнение
        if instance.comment:
            updated_comment = f"{instance.comment}\n\n{header}\n{new_comment}"
        else:
            updated_comment = f"{header}\n{new_comment}"

        # Обновляем только комментарий
        instance.comment = updated_comment
        instance.save(update_fields=['comment'])

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """PATCH запросы тоже обрабатываем через update"""
        return self.update(request, *args, **kwargs)

    @extend_schema(
        summary="Перемикання пріоритету запису",
        description="Змінює статус is_priority на протилежний (True <-> False).",
        request=None,
        responses=JournalRecordSerializer
    )
    @action(detail=True, methods=['post'], url_path='toggle-priority')
    def toggle_priority(self, request, pk=None):
        instance = self.get_object()
        # Инвертируем значение
        instance.is_priority = not instance.is_priority
        # Сохраняем только это поле для оптимизации
        instance.save(update_fields=['is_priority'])

        return Response(self.get_serializer(instance).data)


class UserCreateViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]





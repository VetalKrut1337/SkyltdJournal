from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.models import Client, Vehicle, Service, JournalRecord
from apps.accounts.models import User
from .serializers import (
    ClientSerializer, VehicleSerializer,
    ServiceSerializer, JournalRecordSerializer, UserSerializer
)


class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]

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
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated]

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

        plate = data.get("plate_number")
        brand = data.get("brand")
        model = data.get("model")

        existing_qs = Vehicle.objects.filter(plate_number__iexact=plate)

        # --- если авто с этим номером уже есть, возвращаем его
        if existing_qs.exists():
            obj = existing_qs.first()
            return Response(VehicleSerializer(obj).data, status=200)

        # --- если авто не найдено, но не заполнены brand/model → ошибка
        if not brand or not model:
            return Response(
                {"error": "Для створення нового авто необхідно вказати brand та model"},
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
        data = request.data.copy()

        name = data.get("client_name")
        phone = data.get("phone")
        plate_number = data.get("plate_number")

        client = None
        vehicle = None

        # ---------------------------
        # 1. Автопоиск клиента
        # ---------------------------
        if name or phone:
            qs = Client.objects.all()
            if name:
                qs = qs.filter(name__icontains=name)
            if phone:
                qs = qs.filter(phone__icontains=phone)

            if qs.count() == 1:
                client = qs.first()
                data["client"] = client.id
                if not phone:
                    data["phone"] = client.phone

        # ---------------------------
        # 2. Автопоиск машины
        # ---------------------------
        if plate_number:
            vqs = Vehicle.objects.filter(plate_number__icontains=plate_number)

            if vqs.count() == 1:
                vehicle = vqs.first()
                data["vehicle"] = vehicle.id

                # если не указан клиент → берём из машины
                if not client and vehicle.client:
                    client = vehicle.client
                    data["client"] = client.id
                    if not data.get("phone"):
                        data["phone"] = client.phone

        # ---------------------------
        # 3. Создание нового клиента
        # ---------------------------
        if not client and (name or phone):
            if not name or not phone:
                return Response(
                    {"error": "Для створення нового клієнта потрібно і name, і phone"},
                    status=400
                )
            client = Client.objects.create(name=name, phone=phone)
            data["client"] = client.id

        # ---------------------------
        # 4. Создание новой машины
        # ---------------------------
        brand = data.get("brand")
        model = data.get("model")

        if not vehicle and plate_number:
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
            data["vehicle"] = vehicle.id

        # ---------------------------
        # 5. Создание записи журнала
        # ---------------------------
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response(serializer.data, status=201)

class UserCreateViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]





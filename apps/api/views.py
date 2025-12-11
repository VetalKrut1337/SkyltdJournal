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

    # -----------------------------
    # 1) АВТОПОИСК ПО НОМЕРУ
    # -----------------------------
    @action(detail=False, methods=["GET"])
    def auto_find_by_number(self, request):
        number = request.query_params.get('plate_number')
        if not number:
            return Response({"error": "Параметр plate_number є обов'язковим"}, status=400)

        vehicles = Vehicle.objects.filter(plate_number__icontains=number)

        if not vehicles.exists():
            return Response({"results": []}, status=200)

        return Response({
            "count": vehicles.count(),
            "results": VehicleSerializer(vehicles, many=True).data
        })

    # -----------------------------
    # 2) АВТОПОИСК ПО БРЕНДУ
    # -----------------------------
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

    # -----------------------------
    # 3) АВТОПОИСК ПО МОДЕЛИ
    # -----------------------------
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


    # -----------------------------
    # ПЕРЕОПРЕДЕЛЕННЫЙ create()
    # -----------------------------
    def create(self, request, *args, **kwargs):
        data = request.data.copy()

        # ---- ЛОГИКА ПРОВЕРКИ ----
        plate = data.get("plate_number")
        brand = data.get("brand")
        model = data.get("model")

        existing_qs = Vehicle.objects.filter(plate_number__iexact=plate)

        # 1) Если нашли существующую машину → возвращаем её (чтобы не создавать дубликаты)
        if existing_qs.exists():
            obj = existing_qs.first()
            return Response(VehicleSerializer(obj).data, status=200)

        # 2) Если не нашли → создаём, но проверяем обязательные поля
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
    permission_classes = [permissions.IsAuthenticated]


class UserCreateViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]





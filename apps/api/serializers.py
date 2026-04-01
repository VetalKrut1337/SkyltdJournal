from datetime import timedelta

from rest_framework import serializers
from apps.models import Client, Vehicle, Service, JournalRecord, Appointment
from apps.accounts.models import User


class UserBasicSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'display_name']

    def get_display_name(self, obj):
        full = f"{obj.first_name} {obj.last_name}".strip()
        return full or obj.username


# Используем базовый сериализатор для избежания циклической зависимости
class VehicleBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['id', 'brand', 'model', 'plate_number']


class ClientBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['id', 'name', 'phone']


class VehicleSerializer(serializers.ModelSerializer):
    client = ClientBasicSerializer(read_only=True)
    client_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Vehicle
        fields = ['id', 'brand', 'model', 'plate_number', 'client', 'client_id']
        read_only_fields = ['client']


class ClientSerializer(serializers.ModelSerializer):
    vehicles = VehicleBasicSerializer(many=True, read_only=True)

    class Meta:
        model = Client
        fields = ['id', 'name', 'phone', 'vehicles']


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name', 'is_active']


class JournalRecordSerializer(serializers.ModelSerializer):
    client = ClientBasicSerializer(read_only=True)
    vehicle = VehicleBasicSerializer(read_only=True)
    service = ServiceSerializer(read_only=True)
    services = ServiceSerializer(many=True, read_only=True)

    client_id = serializers.IntegerField(write_only=True, required=False)
    vehicle_id = serializers.IntegerField(write_only=True, required=False)
    service_id = serializers.IntegerField(write_only=True, required=False)
    service_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = JournalRecord
        fields = [
            'id',
            'date',
            'department',
            'is_priority',
            'client',
            'phone',
            'vehicle',
            'service',
            'services',
            'comment',
            'client_id',
            'vehicle_id',
            'service_id',
            'service_ids',
        ]
        read_only_fields = ['client', 'vehicle', 'service', 'services']


class AppointmentSerializer(serializers.ModelSerializer):
    # --- READ ---
    client = serializers.SerializerMethodField()
    vehicle = VehicleBasicSerializer(read_only=True)
    services = ServiceSerializer(many=True, read_only=True)

    users = UserBasicSerializer(many=True, read_only=True)
    users_display = serializers.CharField(read_only=True)

    # --- WRITE ---
    client_id = serializers.IntegerField(write_only=True, required=False)
    vehicle_id = serializers.IntegerField(write_only=True, required=False)

    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=True,
        min_length=1,
    )

    service_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        default=list,
    )

    class Meta:
        model = Appointment
        fields = [
            'id',
            'users',
            'users_display',
            'client',
            'vehicle',
            'services',
            'start_time',
            'duration_minutes',
            'description',
            'status',
            'created_at',
            'updated_at',
            'client_id',
            'vehicle_id',
            'user_ids',
            'service_ids',
        ]
        read_only_fields = [
            'users',
            'client',
            'vehicle',
            'services',
            'created_at',
            'updated_at'
        ]

    # =========================================
    # CLIENT FALLBACK (🔥 ключевой фикс)
    # =========================================
    def get_client(self, obj):
        if obj.client:
            return ClientBasicSerializer(obj.client).data

        if obj.vehicle and obj.vehicle.client:
            return ClientBasicSerializer(obj.vehicle.client).data

        return None

    # =========================================
    # VALIDATION
    # =========================================
    def validate_user_ids(self, value):
        if not value:
            raise serializers.ValidationError("Нужно выбрать хотя бы одного сотрудника.")

        if len(set(value)) != len(value):
            raise serializers.ValidationError("Сотрудники не должны повторяться.")

        users_qs = User.objects.filter(id__in=value)

        if users_qs.count() != len(value):
            raise serializers.ValidationError("Один или несколько сотрудников не найдены.")

        if users_qs.filter(is_superuser=True).exists():
            raise serializers.ValidationError("Нельзя выбрать суперадминов.")

        return value

    # =========================================
    # CREATE
    # =========================================
    def create(self, validated_data):
        request = self.context.get("request")
        raw_data = request.data if request else {}

        user_ids = validated_data.pop("user_ids")
        service_ids = validated_data.pop("service_ids", [])
        client_id = validated_data.pop("client_id", None)
        vehicle_id = validated_data.pop("vehicle_id", None)

        plate = raw_data.get("plate_number", "").strip()
        brand = raw_data.get("brand", "").strip()
        model = raw_data.get("model", "").strip()

        client_name = raw_data.get("client_name", "").strip()
        client_phone = raw_data.get("client_phone", "").strip()

        force = str(raw_data.get("force", "")).lower() in ("1", "true", "yes")

        start_time = validated_data["start_time"]
        duration = validated_data["duration_minutes"]
        end_time = start_time + timedelta(minutes=duration)

        # --- CLIENT ---
        client = None

        if client_id:
            client = Client.objects.filter(id=client_id).first()

        if not client and (client_name or client_phone):
            client = Client.objects.create(
                name=client_name or "—",
                phone=client_phone or None,
            )

        # --- VEHICLE ---
        vehicle = None

        if vehicle_id:
            vehicle = Vehicle.objects.filter(id=vehicle_id).first()

        if not vehicle:
            if not brand or not model:
                raise serializers.ValidationError({
                    "vehicle": "Нужно выбрать авто или указать бренд и модель."
                })

            vehicle, _ = Vehicle.objects.get_or_create(
                plate_number=plate or "-",
                brand=brand,
                model=model,
                client=client,
            )

        elif client and not vehicle.client:
            vehicle.client = client
            vehicle.save(update_fields=["client"])

        if not client and vehicle and vehicle.client:
            client = vehicle.client

        # --- CONFLICT CHECK ---
        conflict_qs = Appointment.objects.filter(
            vehicle=vehicle,
            start_time__lt=end_time,
            start_time__gt=start_time - timedelta(days=1),
        )

        if conflict_qs.exists() and not force:
            raise serializers.ValidationError({
                "has_conflicts": True,
                "conflicts": AppointmentSerializer(conflict_qs, many=True).data,
                "message": "Есть пересечения. Всё равно создать?"
            })

        # --- CREATE ---
        appointment = Appointment.objects.create(
            client=client,
            vehicle=vehicle,
            **validated_data,
        )

        appointment.users.set(user_ids)

        if service_ids:
            services = Service.objects.filter(id__in=service_ids, is_active=True)
            appointment.services.set(services)

        return appointment

    # =========================================
    # UPDATE
    # =========================================
    def update(self, instance, validated_data):
        request = self.context.get("request")
        raw_data = request.data if request else {}

        user_ids = validated_data.pop("user_ids", None)
        service_ids = validated_data.pop("service_ids", None)
        client_id = validated_data.pop("client_id", None)
        vehicle_id = validated_data.pop("vehicle_id", None)

        client_name = raw_data.get("client_name", "").strip()
        client_phone = raw_data.get("client_phone", "").strip()

        # --- USERS ---
        if user_ids is not None:
            instance.users.set(user_ids)

        # --- SERVICES ---
        if service_ids is not None:
            services = Service.objects.filter(id__in=service_ids, is_active=True)
            instance.services.set(services)

        # --- CLIENT ---
        client = instance.client

        if client_id:
            client = Client.objects.filter(id=client_id).first()

        elif client_name or client_phone:
            client = Client.objects.create(
                name=client_name or "—",
                phone=client_phone or None,
            )

        # --- VEHICLE ---
        vehicle = instance.vehicle

        if vehicle_id:
            vehicle = Vehicle.objects.filter(id=vehicle_id).first()

        # если у машины нет клиента — привяжем
        if vehicle and client and not vehicle.client:
            vehicle.client = client
            vehicle.save(update_fields=["client"])

        # fallback клиента
        if not client and vehicle and vehicle.client:
            client = vehicle.client

        # --- APPLY ---
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.client = client
        instance.vehicle = vehicle
        instance.save()

        return instance


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'first_name', 'last_name', 'position']

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

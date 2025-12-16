from rest_framework import serializers
from apps.models import Client, Vehicle, Service, JournalRecord
from apps.accounts.models import User

# Используем базовый сериализатор для избежания циклической зависимости
class VehicleBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['id', 'brand', 'model', 'plate_number']


class VehicleSerializer(serializers.ModelSerializer):
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
    client_id = serializers.IntegerField(write_only=True, required=False)
    vehicle_id = serializers.IntegerField(write_only=True, required=False)
    service_id = serializers.IntegerField(write_only=True, required=False)

    # ввод новых данных (если не существует)
    client_name = serializers.CharField(write_only=True, required=False)
    client_phone = serializers.CharField(write_only=True, required=False)
    vehicle_brand = serializers.CharField(write_only=True, required=False)
    vehicle_model = serializers.CharField(write_only=True, required=False)
    vehicle_plate = serializers.CharField(write_only=True, required=False)

    client = ClientSerializer(read_only=True)
    vehicle = VehicleSerializer(read_only=True)
    service = ServiceSerializer(read_only=True)

    class Meta:
        model = JournalRecord
        fields = [
            'id',
            'date',
            'department',

            # client
            'client', 'client_id', 'client_name', 'client_phone',

            # contact
            'phone',

            # vehicle
            'vehicle', 'vehicle_id', 'vehicle_brand',
            'vehicle_model', 'vehicle_plate',

            # service
            'service', 'service_id',

            'comment',
        ]

    def create(self, validated_data):
        # ---- CLIENT ----
        client = None

        # existing client
        if validated_data.get("client_id"):
            client = Client.objects.filter(id=validated_data["client_id"]).first()

        # create client if not exists
        if not client and validated_data.get("client_name"):
            client, created = Client.objects.get_or_create(
                name=validated_data.get("client_name"),
                defaults={"phone": validated_data.get("client_phone")}
            )

        validated_data["client"] = client

        # ---- VEHICLE (only if department = service) ----

        vehicle = None

        if validated_data.get("vehicle_id"):
            vehicle = Vehicle.objects.filter(id=validated_data["vehicle_id"]).first()

        if not vehicle and validated_data.get("vehicle_plate"):
            vehicle, created = Vehicle.objects.get_or_create(
                plate_number=validated_data["vehicle_plate"],
                defaults={
                    "brand": validated_data.get("vehicle_brand"),
                    "model": validated_data.get("vehicle_model"),
                    "client": client,
                }
            )

        validated_data["vehicle"] = vehicle

        # ---- SERVICE ----

        if validated_data.get("service_id"):
            validated_data["service"] = Service.objects.get(id=validated_data["service_id"])

        # сохранить запись
        return super().create(validated_data)


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

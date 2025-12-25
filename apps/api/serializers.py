from rest_framework import serializers
from apps.models import Client, Vehicle, Service, JournalRecord
from apps.accounts.models import User

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

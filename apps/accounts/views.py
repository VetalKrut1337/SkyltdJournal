from rest_framework import generics, permissions

from rest_framework.serializers import ModelSerializer

from apps.accounts.models import User
from apps.api.serializers import JournalRecordSerializer
from apps.models import JournalRecord


class UserCreateSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "password", "first_name", "last_name", "email"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class UserCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.DjangoModelPermissions]


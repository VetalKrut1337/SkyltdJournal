from django import forms
from apps.models import Client, Vehicle

class ClientCreateForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["name", "phone"]


class VehicleCreateForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ["plate_number", "brand", "model"]


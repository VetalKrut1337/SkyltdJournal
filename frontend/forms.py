from django import forms
from apps.models import Client, Vehicle, JournalRecord


class ClientCreateForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["name", "phone"]


class VehicleCreateForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ["plate_number", "brand", "model"]


class JournalForm(forms.ModelForm):
    class Meta:
        model = JournalRecord
        fields = ["client", "phone", "vehicle", "service", "comment"]
        widgets = {
            "client": forms.Select(attrs={"class": "form-select js-select2-client"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "vehicle": forms.Select(attrs={"class": "form-select js-select2-vehicle"}),
            "service": forms.Select(attrs={"class": "form-select js-select2-service"}),
            "comment": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }
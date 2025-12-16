from django import forms
from apps.models import Client, Vehicle, JournalRecord, Service


class ClientCreateForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["name", "phone"]


class VehicleCreateForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ["plate_number", "brand", "model"]


class JournalForm(forms.ModelForm):
    client = forms.ModelChoiceField(
        queryset=Client.objects.all(),
        required=False,
        widget=forms.Select(attrs={
            "class": "form-select js-select2-client"
        })
    )

    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.all(),
        required=False,
        widget=forms.Select(attrs={
            "class": "form-select js-select2-vehicle"
        })
    )

    service = forms.ModelChoiceField(
        queryset=Service.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={
            "class": "form-select js-select2-service"
        })
    )

    phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control"
        })
    )

    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 3
        })
    )

    class Meta:
        model = JournalRecord
        fields = ("client", "phone", "vehicle", "service", "comment")
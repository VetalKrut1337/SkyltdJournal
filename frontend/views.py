from django.shortcuts import render, redirect
from django.views.generic import TemplateView

from apps.models import Client, Vehicle, JournalRecord

from .forms import ClientCreateForm, VehicleCreateForm

def clients_list(request):
    clients = Client.objects.all().prefetch_related("vehicles")
    free_vehicles = Vehicle.objects.filter(client__isnull=True)

    return render(request, "clients/clients_list.html", {
        "clients": clients,
        "free_vehicles": free_vehicles
    })


def client_create(request):
    if request.method == "POST":
        client_form = ClientCreateForm(request.POST)

        if client_form.is_valid():
            client = client_form.save()

            # Existing vehicle binding
            existing_id = request.POST.get("existing_vehicle")
            if existing_id:
                v = Vehicle.objects.get(id=existing_id)
                v.client = client
                v.save()

            # New vehicle creation
            plate = request.POST.get("plate_number")
            brand = request.POST.get("brand")
            model = request.POST.get("model")

            if plate and brand and model:
                Vehicle.objects.create(
                    plate_number=plate,
                    brand=brand,
                    model=model,
                    client=client
                )

            return redirect("clients_list")

    return redirect("clients_list")


def vehicles_list(request):
    vehicles = Vehicle.objects.select_related("client")
    return render(request, "vehicles/vehicles_list.html", {"vehicles": vehicles})


def vehicle_create(request):
    if request.method == "POST":
        form = VehicleCreateForm(request.POST)
        if form.is_valid():
            form.save()     # создаем машину без владельца
    return redirect("vehicles_list")

class JournalListView(TemplateView):
    template_name = "journals/journal_list.html"

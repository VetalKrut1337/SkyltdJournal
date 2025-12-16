import json

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render, redirect
from django.views.generic import TemplateView

from apps.models import Client, Vehicle, JournalRecord, Service

from .forms import ClientCreateForm, VehicleCreateForm, JournalForm


def clients_list(request):
    return render(request, "clients/clients_list.html")


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
    return render(request, "vehicles/vehicles_list.html")


def vehicle_create(request):
    if request.method == "POST":
        form = VehicleCreateForm(request.POST)
        if form.is_valid():
            form.save()     # создаем машину без владельца
    return redirect("vehicles_list")

def journal_list(request):
    tab = request.GET.get("tab", "sales")
    search = request.GET.get("search", "")
    order = request.GET.get("order", "-date")

    journals = (
        JournalRecord.objects
        .filter(department=tab)
        .select_related("client", "vehicle", "service")
    )

    if search:
        journals = journals.filter(
            Q(client__name__icontains=search) |
            Q(phone__icontains=search) |
            Q(comment__icontains=search)
        )

    journals = journals.order_by(order)

    vehicles_qs = Vehicle.objects.select_related("client")
    vehicles_by_client = {}
    for v in vehicles_qs:
        if not v.client_id:
            continue
        vehicles_by_client.setdefault(v.client_id, []).append({
            "id": v.id,
            "plate": v.plate_number,
            "brand": v.brand,
            "model": v.model,
        })

    return render(request, "journals/journal_list.html", {
        "tab": tab,
        "journals": journals,
        "clients": Client.objects.all(),
        "vehicles": vehicles_qs,
        "vehicles_by_client": json.dumps(vehicles_by_client),
        "services": Service.objects.filter(is_active=True),
        "search": search,
        "order": order,
    })


def journal_create(request):
    if request.method != "POST":
        return redirect("journal_list")

    department = request.POST.get("department")

    # -------- CLIENT --------
    client_id = request.POST.get("client")
    client_name = request.POST.get("client_name")
    phone = request.POST.get("phone")

    client = None
    if client_id:
        client = Client.objects.filter(id=client_id).first()
    else:
        if not client_name or not phone:
            messages.error(request, "Для нового клиента нужно указать имя и телефон")
            return redirect(f"/frontend/journal/?tab={department}")

        client = Client.objects.create(
            name=client_name,
            phone=phone
        )

    # если телефон не введён, но клиент выбран — возьмём телефон клиента
    if not phone and client and client.phone:
        phone = client.phone

    # -------- VEHICLE --------
    vehicle = None
    if department == "service":
        vehicle_id = request.POST.get("vehicle")
        plate = request.POST.get("plate_number")
        brand = request.POST.get("brand")
        model = request.POST.get("model")

        if vehicle_id:
            vehicle = Vehicle.objects.filter(id=vehicle_id).first()
        else:
            if not brand or not model:
                messages.error(request, "Для новой машины нужно указать марку и модель")
                return redirect(f"/frontend/journal/?tab={department}")

            vehicle = Vehicle.objects.create(
                plate_number=plate or "",
                brand=brand,
                model=model,
                client=client
            )

    # -------- SERVICE --------
    service = None
    service_id = request.POST.get("service")
    if department == "service" and service_id:
        service = Service.objects.filter(id=service_id).first()

    # -------- JOURNAL --------
    JournalRecord.objects.create(
        department=department,
        client=client,
        phone=phone,
        vehicle=vehicle,
        service=service,
        comment=request.POST.get("comment")
    )

    return redirect(f"/frontend/journal/?tab={department}")


def services_list(request):
    return render(request, "services/services_list.html")

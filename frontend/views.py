from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render, redirect
from django.views.generic import TemplateView

from apps.models import Client, Vehicle, JournalRecord, Service

from .forms import ClientCreateForm, VehicleCreateForm, JournalForm


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

def journal_list(request):
    tab = request.GET.get("tab", "sales")
    search = request.GET.get("search", "")
    order = request.GET.get("order", "-date")

    journals = JournalRecord.objects.filter(department=tab)

    if search:
        journals = journals.filter(
            Q(client__name__icontains=search) |
            Q(phone__icontains=search) |
            Q(comment__icontains=search)
        )

    journals = journals.order_by(order)

    form = JournalForm()
    return render(request, "journals/journal_list.html", {
        "tab": tab,
        "journals": journals,
        "form": form,
        "search": search,
        "order": order,
    })


def journal_create(request):
    if request.method == "POST":
        department = request.POST.get("department")
        client_id = request.POST.get("client")
        client_name = request.POST.get("client_name")  # для нового клиента
        phone = request.POST.get("phone")

        vehicle_id = request.POST.get("vehicle")
        brand = request.POST.get("brand")
        model = request.POST.get("model")
        service_id = request.POST.get("service")

        comment = request.POST.get("comment")

        # ==== КЛИЕНТ ====
        client = None
        if client_id:
            client = Client.objects.filter(id=client_id).first()
        else:
            if client_name and phone:
                client = Client.objects.create(name=client_name, phone=phone)
            else:
                messages.error(request, "Для нового клиента нужно указать имя и телефон")
                return redirect(f"/frontend/journal/?tab={department}")

        # ==== МАШИНА ====
        vehicle = None
        if department == "service":
            if vehicle_id:
                vehicle = Vehicle.objects.filter(id=vehicle_id).first()
            elif brand and model:
                vehicle = Vehicle.objects.create(
                    brand=brand,
                    model=model,
                    plate_number="",  # пустое поле
                    client=client
                )

        # ==== СЕРВИС ====
        service = None
        if department == "service" and service_id:
            service = Service.objects.filter(id=service_id).first()

        # ==== СОЗДАНИЕ ЖУРНАЛА ====
        JournalRecord.objects.create(
            department=department,
            client=client,
            phone=phone,
            vehicle=vehicle,
            service=service,
            comment=comment
        )

    return redirect(f"/frontend/journal/?tab={department}")


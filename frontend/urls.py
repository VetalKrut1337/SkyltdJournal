from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from .views import clients_list, client_create, vehicles_list, vehicle_create, journal_list, journal_create, services_list

urlpatterns = [
    path("clients/", login_required(clients_list), name="clients_list"),
    path("clients/create/", login_required(client_create), name="client_create"),

    # login/logout
    path("login/", LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("vehicles/", login_required(vehicles_list), name="vehicles_list"),
    path("vehicles/create/", login_required(vehicle_create), name="vehicle_create"),
    path("journal/", login_required(journal_list), name="journal_list"),
    path("journal/create/", login_required(journal_create), name="journal_create"),
    path("services/", login_required(services_list), name="services_list"),
]

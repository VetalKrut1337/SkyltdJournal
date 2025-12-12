from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from .views import clients_list, client_create, vehicles_list, vehicle_create, journal_list, journal_create

urlpatterns = [
    path("clients/", clients_list, name="clients_list"),
    path("clients/create/", client_create, name="client_create"),

    # login/logout
    path("login/", LoginView.as_view(template_name="frontend/login.html"), name="login"),
    path("logout/", LogoutView.as_view(next_page="/login/"), name="logout"),
    path("vehicles/", vehicles_list, name="vehicles_list"),
    path("vehicles/create/", vehicle_create, name="vehicle_create"),
    path("journal/", journal_list, name="journal_list"),
    path("journal/create/", journal_create, name="journal_create"),
]

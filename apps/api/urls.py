from rest_framework.routers import DefaultRouter
from .views import (
    ClientViewSet, VehicleViewSet, ServiceViewSet,
    JournalRecordViewSet, UserCreateViewSet,
    AppointmentViewSet,
)

router = DefaultRouter()

router.register('clients', ClientViewSet)
router.register('vehicles', VehicleViewSet)
router.register('services', ServiceViewSet)
router.register('journals', JournalRecordViewSet)
router.register('users', UserCreateViewSet)
router.register('appointments', AppointmentViewSet, basename='appointments')

urlpatterns = router.urls

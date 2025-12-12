from rest_framework.routers import DefaultRouter
from .views import (
    ClientViewSet, VehicleViewSet, ServiceViewSet,
    JournalRecordViewSet, UserCreateViewSet
)

router = DefaultRouter()

router.register('clients', ClientViewSet)
router.register('vehicles', VehicleViewSet)
router.register('services', ServiceViewSet)
router.register('journals', JournalRecordViewSet)
router.register('users', UserCreateViewSet)

urlpatterns = router.urls

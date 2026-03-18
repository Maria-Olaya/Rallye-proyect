from rest_framework.routers import DefaultRouter
from core.views import SedeViewSet, LocalViewSet

router = DefaultRouter()
router.register("sedes", SedeViewSet, basename="sede")
router.register("locales", LocalViewSet, basename="local")

urlpatterns = router.urls

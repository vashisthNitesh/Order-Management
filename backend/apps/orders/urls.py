from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, notification_poll

router = DefaultRouter()
router.register('', OrderViewSet, basename='order')

urlpatterns = [
    path('notifications/poll/', notification_poll, name='notification_poll'),
    path('', include(router.urls)),
]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, MenuItemViewSet

router = DefaultRouter()
router.register('categories', CategoryViewSet, basename='category')
router.register('items', MenuItemViewSet, basename='menuitem')

urlpatterns = [
    path('', include(router.urls)),
]

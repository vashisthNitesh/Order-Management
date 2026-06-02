from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RestaurantViewSet, TableViewSet

router = DefaultRouter()
router.register('', RestaurantViewSet, basename='restaurant')

table_router = DefaultRouter()
table_router.register('', TableViewSet, basename='table')

urlpatterns = [
    path('', include(router.urls)),
    path('tables/', include(table_router.urls)),
]

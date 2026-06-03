from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    # Django admin
    path('django-admin/', admin.site.urls),

    # API schema (kept for reference)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # REST API endpoints
    path('api/auth/', include('apps.authentication.urls')),
    path('api/restaurants/', include('apps.restaurants.urls')),
    path('api/menu/', include('apps.menu.urls')),
    path('api/orders/', include('apps.orders.urls')),
    path('api/staff/', include('apps.staff.urls')),
    path('api/offers/', include('apps.offers.urls')),

    # Web (template-based) interface
    path('', include('apps.web.urls', namespace='web')),
]

# Redirect root to admin panel
urlpatterns += [
    path('', lambda r: redirect('web:admin_dashboard')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

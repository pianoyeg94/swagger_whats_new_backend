from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse


urlpatterns = [
    path('v1/', include('apps.accounts.api.urls')),
    path('v1/', include('apps.swagger_projects.api.urls')),
    # for DRF's API browser
    path('auth/', include('rest_framework.urls')),
    # for kubernetes readiness and liveness probes
    path('healthz/', lambda request: HttpResponse()),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

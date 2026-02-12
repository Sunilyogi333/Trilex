"""
URL configuration for backend project.
"""

import os
from django.conf import settings
from django.contrib import admin
from django.http import FileResponse
from django.urls import path, include

from drf_spectacular.views import (
    SpectacularSwaggerView,
    SpectacularRedocView,
)

# Serve Custom WebSocket OpenAPI YAML
def custom_openapi_yaml(request):
    file_path = os.path.join(
        settings.BASE_DIR,
        "docs",
        "chat-websocket-openapi.yaml",
    )
    return FileResponse(open(file_path, "rb"), content_type="application/yaml")


urlpatterns = [
    path("admin/", admin.site.urls),

    # 🔥 Custom WebSocket OpenAPI YAML
    path("api/openapi.yaml", custom_openapi_yaml, name="custom-openapi-yaml"),

    # Swagger UI
    path(
        "api/docs/swagger/",
        SpectacularSwaggerView.as_view(url_name="custom-openapi-yaml"),
        name="swagger-ui",
    ),

    # Redoc UI
    path(
        "api/docs/redoc/",
        SpectacularRedocView.as_view(url_name="custom-openapi-yaml"),
        name="redoc-ui",
    ),

    # REST APIs
    path("api/auth/", include("accounts.urls")),
    path("api/clients/", include("clients.urls")),
    path("api/lawyers/", include("lawyers.urls")),
    path("api/firms/", include("firms.urls")),
    path("api/cases/", include("cases.urls")),
    path("api/addresses/", include("addresses.urls")),
    path("api/media/", include("media.urls")),
    path("api/bookings/", include("bookings.urls")),
    path("api/ai-assistant/", include("ai_assistant.urls")),
    path("api/chat/", include("chat.urls")),
]

urlpatterns += [
    path("", include("accounts.api.urls_dev")),
]

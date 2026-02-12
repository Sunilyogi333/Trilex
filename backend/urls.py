"""
URL configuration for backend project.
"""

import os
from django.conf import settings
from django.contrib import admin
from django.http import FileResponse, HttpResponse
from django.urls import path, include

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

# -------------------------------
# Serve WebSocket OpenAPI YAML
# -------------------------------
def websocket_docs_yaml(request):
    file_path = os.path.join(
        settings.BASE_DIR,
        "docs",
        "chat-websocket-openapi.yaml",
    )

    if not os.path.exists(file_path):
        return HttpResponse("WebSocket docs not found", status=404)

    return FileResponse(open(file_path, "rb"), content_type="application/yaml")


urlpatterns = [
    path("admin/", admin.site.urls),

    # REST OpenAPI
    path("api/openapi.json", SpectacularAPIView.as_view(), name="openapi-schema"),

    path(
        "api/docs/swagger/",
        SpectacularSwaggerView.as_view(url_name="openapi-schema"),
        name="swagger-ui",
    ),

    path(
        "api/docs/redoc/",
        SpectacularRedocView.as_view(url_name="openapi-schema"),
        name="redoc-ui",
    ),

    path(
        "api/docs/websocket-ui/",
        SpectacularSwaggerView.as_view(url_name="websocket-docs"),
        name="websocket-ui",
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

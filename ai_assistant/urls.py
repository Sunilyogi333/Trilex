from django.urls import path
from ai_assistant.api.views import AIQueryView

urlpatterns = [
    path("query/", AIQueryView.as_view(), name="ai-query"),
]

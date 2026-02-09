from django.urls import path
from ai_assistant.api.views import (
    AIQueryView, AIQueryHistoryListView)

urlpatterns = [
    path("query/", AIQueryView.as_view(), name="ai-query"),
        path("history/", AIQueryHistoryListView.as_view(), name="ai-history"),

]

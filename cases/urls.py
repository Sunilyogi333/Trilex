from django.urls import path

from cases.api.views import (
    CaseCategoryListCreateAPIView,
    CaseCategoryDetailAPIView,
)

urlpatterns = [
    path(
        "categories/",
        CaseCategoryListCreateAPIView.as_view(),
        name="cases-category-list-create",
    ),
    path(
        "categories/<uuid:pk>/",
        CaseCategoryDetailAPIView.as_view(),
        name="cases-category-detail",
    ),
]

from django.urls import path

from case.api.views import (
    CaseCategoryListCreateAPIView,
    CaseCategoryDetailAPIView,
)

urlpatterns = [
    path(
        "categories/",
        CaseCategoryListCreateAPIView.as_view(),
        name="case-category-list-create",
    ),
    path(
        "categories/<uuid:pk>/",
        CaseCategoryDetailAPIView.as_view(),
        name="case-category-detail",
    ),
]

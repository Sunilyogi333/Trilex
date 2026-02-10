from django.urls import path

from cases.api.views.case_category_views import (
    CaseCategoryListCreateAPIView,
    CaseCategoryDetailAPIView,
)
from cases.api.views.case_views import (
    CaseCreateView,
    CaseDetailView,
    CaseUpdateView,
)
from cases.api.views.case_lawyer_views import CaseLawyerAssignView
from cases.api.views.case_document_views import (
    CaseDocumentCreateView,
    CaseDocumentListView,
)
from cases.api.views.case_date_views import CaseDateCreateView

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
    path("", CaseCreateView.as_view()),
    path("<uuid:case_id>/", CaseDetailView.as_view()),
    path("<uuid:case_id>/update/", CaseUpdateView.as_view()),

    path("<uuid:case_id>/assign-lawyer/", CaseLawyerAssignView.as_view()),

    path("<uuid:case_id>/documents/", CaseDocumentListView.as_view()),
    path("<uuid:case_id>/documents/upload/", CaseDocumentCreateView.as_view()),

    path("<uuid:case_id>/dates/", CaseDateCreateView.as_view()),
]
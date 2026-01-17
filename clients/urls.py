from django.urls import path
from clients.api.views import (
    ClientIDVerificationView,
    ClientIDVerificationMeView
)
from clients.api.admin_views import (
    AdminClientVerificationListView,
    AdminClientVerificationActionView
)

urlpatterns = [
    # client
    path("id-verification/", ClientIDVerificationView.as_view()),
    path("id-verification/me/", ClientIDVerificationMeView.as_view()),

    # admin
    path(
        "admin/id-verifications/",
        AdminClientVerificationListView.as_view()
    ),
    path(
        "admin/id-verifications/<uuid:verification_id>/<str:action>/",
        AdminClientVerificationActionView.as_view()
    ),
]

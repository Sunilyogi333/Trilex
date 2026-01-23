from django.urls import path
from accounts.api.views import DevDeleteAccountView

urlpatterns = [
    path("dev/delete-account/", DevDeleteAccountView.as_view()),
]
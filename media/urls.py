from django.urls import path
from media.api.views import ImageUploadView

urlpatterns = [
    path("upload/", ImageUploadView.as_view()),
]

from django.urls import re_path
from chat.consumers import SocketConsumer

websocket_urlpatterns = [
    re_path(r"ws/socket/$", SocketConsumer.as_asgi()),
]

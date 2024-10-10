from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/audio/', consumers.AudioStreamConsumer.as_asgi()),
]
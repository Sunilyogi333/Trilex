from django.urls import path

from chat.api.views import (
    CreateOrGetRoomView,
    MyChatRoomsView,
    RoomMessagesView,
    MarkRoomAsReadView,
    AddLawyerToRoomView,
    RemoveLawyerFromRoomView,
)

urlpatterns = [
    path("rooms/<uuid:booking_id>/", CreateOrGetRoomView.as_view()),
    path("rooms/", MyChatRoomsView.as_view()),
    path("rooms/<uuid:room_id>/messages/", RoomMessagesView.as_view()),
    path("rooms/<uuid:room_id>/mark-read/", MarkRoomAsReadView.as_view()),
    path("rooms/<uuid:room_id>/add-lawyer/", AddLawyerToRoomView.as_view()),
    path("rooms/<uuid:room_id>/remove-lawyer/", RemoveLawyerFromRoomView.as_view()),
]

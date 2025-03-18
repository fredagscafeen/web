from django.urls import path, re_path

from events.views import EventFeed, Events, EventView

urlpatterns = [
    path("", Events.as_view(), name="events"),
    re_path(r"^(?P<event_id>\d+)$", EventView.as_view(), name="event"),
]

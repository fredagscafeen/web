from django.urls import include, path
from rest_framework import routers

from api.views import (
    BartenderViewSet,
    BeerTypeViewSet,
    BreweryViewSet,
    ForwardedMailStatusView,
    IncomingMailIngestView,
    IsBartenderView,
    ItemViewSet,
    LastModifiedView,
    MailingListsView,
    MailingListView,
    PrintStatusView,
)

router = routers.DefaultRouter()
router.register(r"items", ItemViewSet, "items")
router.register(r"breweries", BreweryViewSet, "breweries")
router.register(r"beerTypes", BeerTypeViewSet)
router.register(r"bartenders", BartenderViewSet)

urlpatterns = [
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("last-modified/", LastModifiedView.as_view(), name="last-modified"),
    path("is-bartender/<username>/", IsBartenderView.as_view(), name="is_bartender"),
    path("print_status/<job_id>/", PrintStatusView.as_view(), name="print_status"),
    path("mailinglists/", MailingListsView.as_view(), name="mailing_lists"),
    path(
        "mailinglists/<mailing_list_name>/",
        MailingListView.as_view(),
        name="mailing_list_detail",
    ),
    path(
        "monitoring/incoming-mails/",
        IncomingMailIngestView.as_view(),
        name="incoming_mail_ingest",
    ),
    path(
        "monitoring/forwarded-mails/<int:pk>/",
        ForwardedMailStatusView.as_view(),
        name="forwarded_mail_status",
    ),
]

urlpatterns += router.urls

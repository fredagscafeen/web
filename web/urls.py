from django.urls import include, path
from django.views.generic.base import RedirectView

from bartab.views import BarTab
from bartenders.views import (
    Ballots,
    BallotsUpdate,
    Barplan,
    BartenderInfo,
    BartenderList,
    Board,
    Index,
    UserBarplan,
    UserDepositShifts,
)
from events.views import EventFeed
from guides.views import Guides
from items.views import Items, Scanner
from udlejning.views import (
    Udlejninger,
    UdlejningerBoardGameCart,
    UdlejningerGrill,
    UdlejningerProjector,
    UdlejningerSpeakers,
    UdlejningerTent,
)
from web.views import About, Login, email_login_view, logout_view

urlpatterns = [
    path("about/", About.as_view(), name="about"),
    path("bartenders/", BartenderList.as_view(), name="bartenders"),
    path("barplan/", Barplan.as_view(), name="barplan"),
    path("barplan/shifts.ics", UserBarplan(), name="shifts_feed"),
    path("barplan/shifts/<username>.ics", UserBarplan(), name="user_shifts"),
    path("barplan/deposit_shifts.ics", UserDepositShifts(), name="deposit_shifts_feed"),
    path("barplan/deposit_shifts/<username>.ics", UserDepositShifts()),
    path(
        "barplan/<username>/", RedirectView.as_view(pattern_name="user_shifts")
    ),  # Old URLs, redirect
    path("prices/", Items.as_view(), name="prices"),
    path("scanner/", Scanner.as_view()),
    path("board/", Board.as_view(), name="board"),
    path("", Index.as_view(), name="index"),
    path("profile/", BartenderInfo.as_view(), name="profile"),
    path("vote/", Ballots.as_view(), name="ballots"),
    path("vote/update/", BallotsUpdate.as_view(), name="ballots_update"),
    path("bartab/", BarTab.as_view(), name="bartab"),
    path("events/", include("events.urls")),
    path("events.ics", EventFeed(), name="event_feed"),
    path("login/", Login.as_view(), name="login"),
    path("login/<email>/<token>/", email_login_view, name="email_login"),
    path("logout/", logout_view, name="logout"),
    path("udlejning/", Udlejninger.as_view(), name="udlejning"),
    path("udlejningGrill/", UdlejningerGrill.as_view(), name="udlejningGrill"),
    path(
        "udlejningProjector/", UdlejningerProjector.as_view(), name="udlejningProjector"
    ),
    path("udlejningSpeakers/", UdlejningerSpeakers.as_view(), name="udlejningSpeakers"),
    path(
        "udlejningBoardGameCart/",
        UdlejningerBoardGameCart.as_view(),
        name="udlejningBoardGameCart",
    ),
    path(
        "udlejningTent/",
        UdlejningerTent.as_view(),
        name="udlejningTent",
    ),
    path("guides/", Guides.as_view(), name="guides"),
    path("gallery/", include("gallery.urls")),
]

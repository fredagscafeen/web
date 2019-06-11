from django.urls import path
from django.views.generic.base import RedirectView

from web.views import Contact, Guides, Login, email_login_view, logout_view
from bartenders.views import Index, BartenderList, Barplan, UserBarplan, Board, \
    UserDepositShifts, BartenderInfo
from bartab.views import BarTab
from events.views import Events, EventFeed
from guides.update import update_hook
from items.views import Items, Search
from udlejning.views import Udlejninger, UdlejningerGrill

urlpatterns = [
    path('update_hook/', update_hook),
    path('contact/', Contact.as_view()),
    path('bartenders/', BartenderList.as_view()),
    path('barplan/', Barplan.as_view(), name='barplan'),
    path('barplan/shifts.ics', UserBarplan()),
    path('barplan/shifts/<username>.ics', UserBarplan(), name='user_shifts'),
    path('barplan/deposit_shifts.ics', UserDepositShifts()),
    path('barplan/deposit_shifts/<username>.ics', UserDepositShifts()),
    path('barplan/<username>/', RedirectView.as_view(pattern_name='user_shifts')), # Old URLs, redirect
    path('prices/', Items.as_view()),
    path('board/', Board.as_view()),
    path('search/', Search.as_view()),
    path('', Index.as_view()),
    path('profile/', BartenderInfo.as_view(), name='profile'),
    path('bartab/', BarTab.as_view(), name='bartab'),
    path('events/', Events.as_view(), name='events'),
    path('events.ics', EventFeed(), name='event_feed'),
    path('login/', Login.as_view(), name='login'),
    path('login/<email>/<token>/', email_login_view, name='email_login'),
    path('logout/', logout_view, name='logout'),
    path('udlejning/', Udlejninger.as_view()),
    path('udlejningGrill/', UdlejningerGrill.as_view()),
    path('guides/', Guides.as_view(), name='guides'),
]

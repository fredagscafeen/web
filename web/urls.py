from django.urls import path

from web.views import Index, Contact, BartenderList, Barplan, UserBarplan, Items, Board, Search, Udlejninger, \
    UdlejningerGrill, Guides

urlpatterns = [
    path('contact/', Contact.as_view()),
    path('bartenders/', BartenderList.as_view()),
    path('barplan/', Barplan.as_view(), name='barplan'),
    path('barplan/<username>/', UserBarplan()),
    path('prices/', Items.as_view()),
    path('board/', Board.as_view()),
    path('search/', Search.as_view()),
    path('', Index.as_view()),
    path('udlejning/', Udlejninger.as_view()),
    path('udlejningGrill/', UdlejningerGrill.as_view()),
    path('guides/', Guides.as_view()),
]

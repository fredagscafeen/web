from django.conf.urls import url

from web.views import Index, Contact, BartenderList, Barplan, UserBarplan, Items, Board, Search, Udlejninger, UdlejningerGrill, Guides

urlpatterns = [
    url(r'^contact/', Contact.as_view()),
    url(r'^bartenders/', BartenderList.as_view()),
    url(r'^barplan/$', Barplan.as_view()),
    url(r'^barplan/(?P<username>[0-9a-zA-Z]+)/', UserBarplan()),
    url(r'^prices/', Items.as_view()),
    url(r'^board/', Board.as_view()),
    url(r'^search/', Search.as_view()),
    url(r'^$', Index.as_view()),
    url(r'^udlejning/', Udlejninger.as_view()),
    url(r'^udlejningGrill/', UdlejningerGrill.as_view()),
    url(r'^guides/', Guides.as_view()),
    ]

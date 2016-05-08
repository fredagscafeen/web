from django.conf.urls import url

from web.views import Index, Contact, BartenderList, Barplan, Items, Board, Foo

urlpatterns = [
    url(r'^contact/', Contact.as_view()),
    url(r'^bartenders/', BartenderList.as_view()),
    url(r'^barplan/', Barplan.as_view()),
    url(r'^prices/', Items.as_view()),
    url(r'^board/', Board.as_view()),
    url(r'^search/', Foo.as_view()),
    url(r'^$', Index.as_view()),
    ]

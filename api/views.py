from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import (
    BartenderSerializer,
    BeerTypeSerializer,
    BrewerySerializer,
    ForwardedMailStatusSerializer,
    IncomingMailIngestSerializer,
    ItemSerializer,
    MailingListBartenderSerializer,
    MailingListsSerializer,
    SpamFilterSerializer,
)
from bartenders.models import Bartender
from items.models import BeerType, Brewery, Item
from mail.models import ForwardedMail, MailingList, SpamFilterTLD
from printer.models import Printer


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer


class BreweryViewSet(viewsets.ModelViewSet):
    queryset = Brewery.objects.all()
    serializer_class = BrewerySerializer


class BeerTypeViewSet(viewsets.ModelViewSet):
    queryset = BeerType.objects.all()
    serializer_class = BeerTypeSerializer


class BartenderViewSet(viewsets.ModelViewSet):
    queryset = Bartender.objects.all()
    serializer_class = BartenderSerializer


class LastModifiedView(APIView):
    permission_classes = ()

    def get(self, request, format=None):
        last_modified = None
        for item in Item.objects.all():
            if last_modified is None or item.lastModified > last_modified:
                last_modified = item.lastModified
        return Response(last_modified, status=status.HTTP_200_OK)


class IsBartenderView(APIView):
    permission_classes = ()

    def get(self, request, username, format=None):
        is_bartender = False
        try:
            if Bartender.objects.get(username=username).isActiveBartender:
                is_bartender = True
        except Bartender.DoesNotExist:
            pass
        return Response(is_bartender, status=status.HTTP_200_OK)


class PrintStatusView(APIView):
    required_permissions = ("printer.view_printer",)

    def get(self, request, job_id):
        status, code = Printer.get_status(job_id)
        return Response({"status": status, "code": code})


class IncomingMailIngestView(APIView):
    required_permissions = ("mail.add_incomingmail", "mail.change_incomingmail")

    def post(self, request):
        serializer = IncomingMailIngestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        incoming_mail = serializer.save()
        return Response(
            {"id": incoming_mail.pk, "status": incoming_mail.status},
            status=status.HTTP_200_OK,
        )


class ForwardedMailStatusView(APIView):
    required_permissions = ("mail.change_forwardedmail",)

    def patch(self, request, pk):
        forwarded_mail = get_object_or_404(ForwardedMail, pk=pk)
        serializer = ForwardedMailStatusSerializer(
            forwarded_mail,
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


# Lists all mailing lists with their names without members, does not leak any information about the members of the mailing lists
class MailingListsView(APIView):
    required_permissions = ("mail.view_mailinglist",)

    def get(self, request):
        mailing_lists = MailingList.objects.all()
        serializer = MailingListsSerializer(mailing_lists, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# Lists all members of a mailing list with their emails, requires permission to view mailing list and bartenders, does not leak any information if the mailing list does not exist or if the user does not have permission to view the mailing list
class MailingListView(APIView):
    required_permissions = (
        "mail.view_mailinglist",
        "bartenders.view_bartender",
    )

    def get(self, request, mailing_list_name):
        mailing_list = get_object_or_404(MailingList, name=mailing_list_name)
        serializer = MailingListBartenderSerializer(mailing_list.members, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SpamfilterView(APIView):
    required_permissions = ("mail.view_spamfiltertld",)

    def get(self, request):
        spamfilter_tlds = SpamFilterTLD.objects.all()
        serializer = SpamFilterSerializer(spamfilter_tlds, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

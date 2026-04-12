from django.db import transaction
from rest_framework import serializers

from bartenders.models import Bartender
from items.models import BeerType, Brewery, Item
from mail.models import ForwardedMail, IncomingMail, MailArchive, MailingList


class BrewerySerializer(serializers.ModelSerializer):
    class Meta:
        model = Brewery
        fields = "__all__"


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = "__all__"


class BartenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bartender
        fields = ("id", "name", "username", "isActiveBartender")


class BeerTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BeerType
        fields = "__all__"


class IncomingMailIngestSerializer(serializers.Serializer):
    request_uuid = serializers.UUIDField()
    received_at = serializers.DateTimeField()
    sender = serializers.CharField(max_length=320)
    target = serializers.CharField(max_length=320)
    mailing_list = serializers.SlugRelatedField(
        slug_field="name",
        queryset=MailingList.objects.all(),
        required=False,
        allow_null=True,
    )
    status = serializers.ChoiceField(choices=IncomingMail.Status.choices)
    reason = serializers.CharField(required=False, allow_blank=True, default="")
    s3_object_key = serializers.CharField(max_length=1024)
    expanded_recipients = serializers.ListField(
        child=serializers.CharField(max_length=320),
        required=False,
        default=list,
    )

    def validate(self, attrs):
        if (
            attrs["status"] == IncomingMail.Status.DROPPED
            and not attrs.get("reason", "").strip()
        ):
            raise serializers.ValidationError(
                {"reason": "This field is required when status is DROPPED."}
            )
        return attrs

    @transaction.atomic
    def save(self):
        archive, _ = MailArchive.objects.update_or_create(
            request_uuid=self.validated_data["request_uuid"],
            defaults={"s3_object_key": self.validated_data["s3_object_key"]},
        )
        incoming_mail, _ = IncomingMail.objects.update_or_create(
            mail_archive=archive,
            defaults={
                "received_at": self.validated_data["received_at"],
                "sender": self.validated_data["sender"],
                "target": self.validated_data["target"],
                "mailing_list": self.validated_data.get("mailing_list"),
                "status": self.validated_data["status"],
                "reason": self.validated_data.get("reason", ""),
            },
        )

        initial_attempts = incoming_mail.forward_attempts.filter(
            previous_attempt__isnull=True
        )
        if incoming_mail.status == IncomingMail.Status.PROCESSED:
            initial_attempts.exclude(
                target__in=self.validated_data["expanded_recipients"]
            ).delete()
            existing_targets = set(initial_attempts.values_list("target", flat=True))
            desired_recipients = dict.fromkeys(
                self.validated_data["expanded_recipients"]
            )
            ForwardedMail.objects.bulk_create(
                [
                    ForwardedMail(
                        incoming_mail=incoming_mail,
                        target=recipient,
                        forwarded_at=incoming_mail.received_at,
                        status=ForwardedMail.Status.FORWARDED,
                    )
                    for recipient in desired_recipients
                    if recipient not in existing_targets
                ]
            )
        else:
            initial_attempts.delete()

        return incoming_mail


class ForwardedMailStatusSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=((ForwardedMail.Status.FAILED, "Failed"),))
    reason = serializers.CharField(allow_blank=False, required=True)

    class Meta:
        model = ForwardedMail
        fields = ("status", "reason")


class MailingListBartenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bartender
        fields = ("id", "name", "email")


class MailingListSerializer(serializers.ModelSerializer):
    members = MailingListBartenderSerializer(many=True, read_only=True)

    class Meta:
        model = MailingList
        fields = ("id", "name", "isOnlyInternal", "members")


class MailingListsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MailingList
        fields = ("id", "name", "isOnlyInternal")

import logging
import os
from datetime import date

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.dispatch import receiver
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from model_utils.managers import InheritanceManager
from six import python_2_unicode_compatible
from sorl.thumbnail import get_thumbnail
from versatileimagefield.fields import VersatileImageField
from versatileimagefield.image_warmer import VersatileImageFieldWarmer

from fredagscafeen.settings.base import MEDIA_ROOT
from gallery.utils import file_name, get_exif_date, get_year, slugify

FORCEDORDERMAX = 10000

logger = logging.getLogger(__name__)


@python_2_unicode_compatible
class Album(models.Model):
    class Meta:
        ordering = ["year", "bartenderalbum", "oldFolder", "-publish_date"]
        unique_together = (("year", "slug"),)
        verbose_name = _("Album")
        verbose_name_plural = _("Albummer")

    title = models.CharField(max_length=200, verbose_name=_("Titel"))
    publish_date = models.DateField(
        blank=True, null=True, default=date.today, verbose_name=_("Udgivelsesdato")
    )
    thumbnail = models.ImageField(
        upload_to="galleries", blank=True, null=True, verbose_name=_("Thumbnail")
    )
    bartenderalbum = models.BooleanField(
        default=False,
        verbose_name=_("Bartenderarrangement"),
        help_text=_("Bartenderarrangementer er kun synlige for bartendere"),
    )
    year = models.PositiveSmallIntegerField(default=get_year, verbose_name=_("Årgang"))
    slug = models.SlugField(verbose_name=_("Kort titel"))
    description = models.TextField(blank=True, verbose_name=_("Beskrivelse"))

    oldFolder = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return "%s: %s" % (self.year, self.title)

    def clean(self):
        for m in self.basemedia.all():
            m.save()

        f = self.basemedia.filter(visibility=BaseMedia.PUBLIC).first()
        if f:
            f.save()

    def get_absolute_url(self):
        return reverse("album", kwargs={"year": self.year, "album_slug": self.slug})


@python_2_unicode_compatible
class BaseMedia(models.Model):
    class Meta:
        ordering = ["forcedOrder", "date", "slug"]
        unique_together = (("album", "slug"),)

        # Use the pre-1.6 save(). This is a workaround for
        # https://github.com/TK-IT/web/issues/72 This can be removed when the
        # upstream bug https://code.djangoproject.com/ticket/21670 is closed
        select_on_save = True

    IMAGE = "I"
    VIDEO = "V"
    AUDIO = "A"
    OTHER = "O"
    TYPE_CHOICES = (
        (IMAGE, _("Image")),
        (VIDEO, _("Video")),
        (AUDIO, _("Audio")),
        (OTHER, _("Other")),
    )

    PUBLIC = "public"
    DISCARDED = "discarded"
    SENSITIVE = "sensitive"
    DELETE = "delete"
    NEW = "new"
    VISIBILITY = (
        (PUBLIC, _("Synligt")),
        (DISCARDED, _("Frasorteret")),
        (SENSITIVE, _("Skjult")),
        (DELETE, _("Slet")),
        (NEW, _("Ubesluttet")),
    )

    type = models.CharField(max_length=1, choices=TYPE_CHOICES, default=OTHER)

    objects = InheritanceManager()
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name="basemedia")

    date = models.DateTimeField(null=True, blank=True, verbose_name=_("Dato"))
    visibility = models.CharField(
        max_length=10, choices=VISIBILITY, verbose_name=_("Synlighed"), default=NEW
    )
    caption = models.CharField(max_length=200, blank=True, verbose_name=_("Overskrift"))

    slug = models.SlugField(null=True, blank=True, verbose_name=_("Kort titel"))

    forcedOrder = models.SmallIntegerField(
        default=0,
        validators=[
            MinValueValidator(-FORCEDORDERMAX),
            MaxValueValidator(FORCEDORDERMAX),
        ],
        verbose_name="Rækkefølge",
    )

    def admin_thumbnail(self):
        if self.type == BaseMedia.IMAGE:
            return self.image.admin_thumbnail()

    admin_thumbnail.short_description = _("Thumbnail")

    @property
    def notPublic(self):
        return self.visibility != self.PUBLIC

    def __str__(self):
        return "%s" % (self.slug)

    def get_absolute_url(self):
        return reverse(
            "image",
            kwargs={
                "year": self.album.year,
                "album_slug": self.album.slug,
                "image_slug": self.slug,
            },
        )


class Image(BaseMedia):
    class Meta:
        # Use the pre-1.6 save(). This is a workaround for
        # https://github.com/TK-IT/web/issues/72 This can be removed when the
        # upstream bug https://code.djangoproject.com/ticket/21670 is closed
        select_on_save = True

    objects = models.Manager()
    file = VersatileImageField(upload_to=file_name)

    def admin_thumbnail(self):
        return format_html('<img src="{}" />', get_thumbnail(self.file, "150x150").url)

    admin_thumbnail.short_description = _("Thumbnail")

    def clean(self):
        self.type = BaseMedia.IMAGE

        if self.date == None:
            self.date = get_exif_date(self.file)

        if self.slug == None:
            if self.date == None:
                self.slug = slugify(
                    os.path.splitext(os.path.basename(self.file.name))[0]
                )
            else:
                self.slug = self.date.strftime("%Y%m%d%H%M%S_%f")[
                    : len("YYYYmmddHHMMSS_ff")
                ]

    def save(self, *args, **kwargs):
        """
        This saves the Image, tries to prewarm VersatileImageField and deletes
        itself again if it fails. Ideally this would be done in clean(), but
        VersatileImageField cannot prewarm before it is saved and does not have
        a clean that checks if the warming is bound to succeed.

        """
        super().save(*args, **kwargs)
        image_warmer = VersatileImageFieldWarmer(
            instance_or_queryset=self, rendition_key_set="gallery", image_attr="file"
        )

        num_created, failed_to_create = image_warmer.warm()
        if failed_to_create:

            self.delete()  # Hey! Look at me!

            logger.warning(
                "Prewarming during save() of %s failed. Deleting again." % self
            )
            raise ValidationError("Corrupt image. Deleting")


class GenericFile(BaseMedia):
    class Meta:
        # Use the pre-1.6 save(). This is a workaround for
        # https://github.com/TK-IT/web/issues/72 This can be removed when the
        # upstream bug https://code.djangoproject.com/ticket/21670 is closed
        select_on_save = True

    objects = models.Manager()
    originalFile = models.FileField(upload_to=file_name, blank=True)
    file = models.FileField(upload_to=file_name)

    def clean(self):
        if self.slug == None:
            if self.date == None:
                sep = os.path.splitext(os.path.basename(self.file.name))
                self.slug = slugify(sep[0]) + sep[1]
                self.forcedOrder = FORCEDORDERMAX
            else:
                self.slug = self.date.strftime("%Y%m%d%H%M%S_%f")[
                    : len("YYYYmmddHHMMSS_ff")
                ]


@receiver(models.signals.post_delete, sender=Image)
def deleteImageThumbnails(sender, instance, **kwargs):
    """
    Delete all thumbnails generated by the VersatileImageField.
    """
    logger.debug("deleteImageThumbnails: called with instance: %s." % (instance))
    instance.file.delete_sized_images()
    logger.debug("deleteImageThumbnails: deleting images")

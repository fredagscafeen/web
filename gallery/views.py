import os
from datetime import datetime

from django.contrib.auth.decorators import permission_required
from django.contrib.syndication.views import Feed
from django.core.exceptions import ValidationError
from django.db.models import Count
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from jfu.http import JFUResponse, UploadResponse, upload_receive

from gallery.forms import EditVisibilityForm
from gallery.models import Album, BaseMedia, GenericFile, Image

GALLERY_PERMISSION = "gallery.change_image"


def get_basemedia_count_by_album():
    """
    Return C such that::

        C[v][i] == BaseMedia.objects.filter(visibility=v, album_id=i).count()
    """

    qs = BaseMedia.objects.all()
    qs = qs.order_by().values("album_id", "visibility")
    qs = qs.annotate(count=Count("id"))
    by_visibility = {}
    for record in qs:
        by_album = by_visibility.setdefault(record["visibility"], {})
        by_album[record["album_id"]] = record["count"]
    return by_visibility


def gallery(request, **kwargs):
    count_by_visibility = get_basemedia_count_by_album()
    public_count = count_by_visibility.get(BaseMedia.PUBLIC, {})
    new_count = count_by_visibility.get(BaseMedia.NEW, {})
    edit_visibility = request.user.has_perm(GALLERY_PERMISSION)

    try:
        requested_year = int(kwargs["year"])
    except (KeyError, ValueError):
        requested_year = None

    albums = list(Album.objects.all())
    for album in albums:
        album.count = public_count.get(album.id, 0)
        album.new_count = new_count.get(album.id, 0) if edit_visibility else 0

    # Hide albums with no images
    albums = [a for a in albums if a.count + a.new_count > 0]
    years = set(a.year for a in albums)
    years = sorted(years, reverse=True)

    if requested_year is None:
        if years:
            show_year = max(years)
        else:
            show_year = datetime.now().year
    else:
        show_year = requested_year

    # Hide albums not in show_year
    albums = [a for a in albums if a.year == show_year]

    context = {
        "years": years,
        "show_year": show_year,
        "albums": albums,
    }

    return render(request, "gallery.html", context)


def album(request, year, album_slug):
    album = get_object_or_404(Album, year=year, slug=album_slug)
    files = album.basemedia.filter(visibility=BaseMedia.PUBLIC).select_subclasses()
    context = {"album": album, "files": files}

    edit_visibility = request.user.has_perm(GALLERY_PERMISSION)
    new_file = album.basemedia.filter(visibility=BaseMedia.NEW).first()
    if edit_visibility and new_file:
        if request.POST.get("set_all_new_visible"):
            qs = album.basemedia.filter(visibility=BaseMedia.NEW)
            qs.update(visibility=BaseMedia.PUBLIC)

            return redirect("album", year=year, album_slug=album_slug)

        kwargs = dict(year=album.year, album_slug=album.slug, image_slug=new_file.slug)
        context["edit_visibility_link"] = reverse("image", kwargs=kwargs) + "?v=1"

        qs = album.basemedia.all().order_by()
        qs_visibility = qs.values_list("visibility")
        visibility_counts = dict(qs_visibility.annotate(count=Count("pk")))
        c_public = visibility_counts.pop(BaseMedia.PUBLIC, 0)
        c_discarded = visibility_counts.pop(BaseMedia.DISCARDED, 0)
        c_sensitive = visibility_counts.pop(BaseMedia.SENSITIVE, 0)
        c_delete = visibility_counts.pop(BaseMedia.DELETE, 0)
        c_new = visibility_counts.pop(BaseMedia.NEW, 0)
        if visibility_counts:
            raise ValueError(visibility_counts)
        context["visible_count"] = c_public
        context["hidden_count"] = c_discarded + c_sensitive + c_delete + c_new
        context["new_count"] = c_new
    return render(request, "album.html", context)


def image(request, year, album_slug, image_slug, **kwargs):
    album = get_object_or_404(Album, year=year, slug=album_slug)

    edit_visibility = bool(request.GET.get("v")) and request.user.has_perm(
        GALLERY_PERMISSION
    )

    qs = album.basemedia.all()
    if not edit_visibility:
        qs = qs.filter(visibility=BaseMedia.PUBLIC)
    qs = qs.select_subclasses()
    # list() will force evaluation of the QuerySet. It is now iterable.
    files = list(qs)
    start_file = (
        album.basemedia.filter(album=album, slug=image_slug).select_subclasses().first()
    )
    if edit_visibility:
        form = EditVisibilityForm(files)
        for file, (pk, key) in zip(files, form.basemedias):
            file.visibility_field = form[key]

    if not start_file:
        raise Http404(_("Billedet kan ikke findes"))

    if start_file.notPublic and not edit_visibility:
        raise Http404(_("Billedet kan ikke findes"))

    prev_files = files[1:] + files[:1]
    next_files = files[-1:] + files[:-1]
    file_orders = zip(files, prev_files, next_files)
    file_count = len(files)

    context = {
        "album": album,
        "file_orders": file_orders,
        "start_file": start_file,
        "file_count": file_count,
        "edit_visibility": edit_visibility,
    }
    return render(request, "image.html", context)


@require_POST
@permission_required("gallery.add_image", raise_exception=True)
def upload(request):
    file = upload_receive(request)
    if file is None:
        return UploadResponse(request, {"error": "No file"})
    album = Album.objects.get(id=int(request.POST["object_id"]))
    ext = os.path.splitext(file.name)[1].lower()

    if ext in (".png", ".gif", ".jpg", ".jpeg"):
        instance = Image(file=file, album=album)
    elif ext in (".mp3"):
        instance = GenericFile(file=file, album=album)
        instance.type = BaseMedia.AUDIO
    elif ext in (".mp4"):
        instance = GenericFile(file=file, album=album)
        instance.type = BaseMedia.VIDEO
    else:
        instance = GenericFile(file=file, album=album)
        instance.type = BaseMedia.OTHER

    try:
        instance.full_clean()
        instance.save()
    except ValidationError as exn:
        try:
            error = " ".join(
                "%s: %s" % (k, v) for k, vs in exn.message_dict.items() for v in vs
            )
        except AttributeError:
            error = " ".join(exn.messages)

        jfu_msg = {
            "name": file.name,
            "size": file.size,
            "error": error,
        }
        return UploadResponse(request, jfu_msg)

    jfu_msg = {
        "name": os.path.basename(instance.file.path),
        "size": file.size,
        "url": instance.file.url,
    }
    return UploadResponse(request, jfu_msg)


@require_POST
@permission_required("gallery.delete_image", raise_exception=True)
def upload_delete(request, pk):
    success = True
    try:
        instance = Image.objects.get(pk=pk)
        instance.image.delete(save=False)
        instance.delete()
    except Image.DoesNotExist:
        success = False

    return JFUResponse(request, success)


@require_POST
@permission_required(GALLERY_PERMISSION, raise_exception=True)
def set_visibility(request):
    try:
        form = EditVisibilityForm.from_POST(request.POST)
    except EditVisibilityForm.Missing as exn:
        return HttpResponseBadRequest(str(exn))
    if not form.is_valid():
        return HttpResponseBadRequest(str(form.errors))
    for pk, key in form.basemedias:
        initial = form.fields[key].initial
        value = form.cleaned_data[key]
        if initial != value:
            BaseMedia.objects.filter(pk=pk).update(visibility=value)

    albums = list(Album.objects.filter(pk__in=form.album_pks))

    # Redirect to album
    if albums:
        album = albums[0]
        kwargs = dict(year=album.year, album_slug=album.slug)
        return HttpResponseRedirect(reverse("album", kwargs=kwargs))
    else:
        return HttpResponse(_("Synlighed på givne billeder er blevet opdateret"))


class AlbumFeed(Feed):
    title = _("Fredagscaféens billedalbummer")

    def link(self):
        return reverse("gallery_index")

    description = _("Feed med nye billedalbummer fra Fredagscaféens begivenheder.")

    def items(self):
        nonempties = Album.objects.filter(
            basemedia__visibility=BaseMedia.PUBLIC
        ).distinct()
        return nonempties.order_by("-publish_date")

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.description

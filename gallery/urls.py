from django.urls import path, re_path

import gallery.views as views

urlpatterns = [
    # Gallery overview
    path("", views.gallery, name="gallery_index"),
    re_path(r"^(?P<year>\d+)$", views.gallery, name="year"),
    # Album overview
    re_path(r"^(?P<year>\d+)/(?P<album_slug>[^/]+)$", views.album, name="album"),
    # Single images
    re_path(
        r"^(?P<year>\d+)/(?P<album_slug>[^/]+)/(?P<image_slug>[^/]+)$",
        views.image,
        name="image",
    ),
    # Bulk-update BaseMedia.visibility
    re_path(r"^set_visibility/$", views.set_visibility, name="set_image_visibility"),
    # JFU upload
    re_path(r"^upload/", views.upload, name="jfu_upload"),
    # RSS feed
    re_path(r"^album\.rss$", views.AlbumFeed(), name="album_rss"),
]

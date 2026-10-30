from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib import admin
from django.test import RequestFactory, TestCase, override_settings

from .views import pdf_preview


class PdfPreviewTest(TestCase):
    def test_get_creates_media_root_before_copying_generated_pdf(self):
        request = RequestFactory().get("/admin/items/item/generate-shelf-labels/")
        latex_context = type(
            "LatexContext",
            (),
            {"file_name": "shelf_labels", "file_path": "unused"},
        )()

        with TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                with TemporaryDirectory() as work_dir:
                    generated_pdf = Path(work_dir) / "shelf_labels.pdf"
                    generated_pdf.write_bytes(b"%PDF-1.4 test")

                    with patch(
                        "printer.views.generate_pdf", return_value=str(generated_pdf)
                    ):
                        with patch("printer.views.TemplateResponse") as response:
                            pdf_preview(request, admin.site, latex_context)

                output_pdf = Path(media_root) / "shelf_labels.pdf"
                self.assertEqual(output_pdf.read_bytes(), b"%PDF-1.4 test")
        response.assert_called_once()

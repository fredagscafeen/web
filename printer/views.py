import shutil
from subprocess import CalledProcessError
from tempfile import TemporaryDirectory

from django.conf import settings
from django.http import HttpResponse
from django.template.response import TemplateResponse

from .forms import PrintForm
from .latex import LatexError, generate_pdf
from .models import Printer


def pdf_preview(request, admin_site, latex_context):
    TEST_PDF_PATH = "/usr/share/cups/data/testprint"

    file_name = latex_context.file_name
    pdf_path = f"{settings.MEDIA_ROOT}/{file_name}.pdf"

    form = PrintForm()

    if request.method == "POST":
        form = PrintForm(request.POST)
        if form.is_valid():
            printer = form.cleaned_data["printer"]
            try:
                if request.POST.get("print_test_submit"):
                    job_id = printer.print(TEST_PDF_PATH, inside_dokku=False)
                else:
                    job_id = printer.print(pdf_path)
            except CalledProcessError as e:
                return HttpResponse(
                    f"""Got unexpected exit code {e.returncode} from running:
{e.cmd}

stdout:
{e.stdout}

stderr:
{e.stderr}""",
                    content_type="text/plain",
                )

            context = dict(
                # Include common variables for rendering the admin template.
                admin_site.each_context(request),
                # Anything else you want in the context...
                printer_name=printer.name,
                job_id=job_id,
            )
            return TemplateResponse(request, "print_status.html", context)

    if request.method == "GET":
        with TemporaryDirectory() as d:
            try:
                fname = generate_pdf(d, latex_context)
                shutil.copy(fname, pdf_path)
            except LatexError as e:
                with open(f"{d}/{file_name}.tex") as f:
                    source = f.read()

                error_text = f"""==== Got an error from latexmk ====

== latexmk output ==

{e.message}

== LaTeX source ==

{source}"""
                return HttpResponse(error_text, content_type="text/plain")

    context = dict(
        # Include common variables for rendering the admin template.
        admin_site.each_context(request),
        # Anything else you want in the context...
        form=form,
        connected=Printer.is_connected(),
        pdf_url=f"{settings.MEDIA_URL}/{file_name}.pdf",
    )
    return TemplateResponse(request, "pdf_preview.html", context)

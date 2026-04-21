import subprocess
from pathlib import Path

from django.template.loader import render_to_string


class LatexError(Exception):
    def __init__(self, message):
        self.message = message


def _get_render_context(work_dir, latex_context):
    get_context_for_work_dir = getattr(latex_context, "get_context_for_work_dir", None)
    if callable(get_context_for_work_dir):
        return get_context_for_work_dir(work_dir)

    return latex_context.get_context()


def generate_pdf(work_dir, latex_context):
    file_name = latex_context.file_name
    with (Path(work_dir) / f"{file_name}.tex").open("w") as f:
        latex = render_to_string(
            latex_context.file_path, _get_render_context(work_dir, latex_context)
        )
        f.write(latex)

    p = subprocess.run(
        ["latexmk", "-halt-on-error", "-pdf", f"{file_name}.tex"],
        cwd=work_dir,
        stdout=subprocess.PIPE,
    )
    if p.returncode != 0:
        raise LatexError(str(p.stdout, "utf-8"))

    return work_dir + f"/{file_name}.pdf"

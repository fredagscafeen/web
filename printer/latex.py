import subprocess
from pathlib import Path

from django.template.loader import render_to_string


class LatexError(Exception):
    def __init__(self, message):
        self.message = message


def generate_pdf(work_dir, latex_context):
    file_name = latex_context.file_name
    with (Path(work_dir) / f"{file_name}.tex").open("w") as f:
        latex = render_to_string(latex_context.file_path, latex_context.get_context())
        f.write(latex)

    p = subprocess.run(
        ["latexmk", "-halt-on-error", "-pdf", f"{file_name}.tex"],
        cwd=work_dir,
        stdout=subprocess.PIPE,
    )
    if p.returncode != 0:
        raise LatexError(str(p.stdout, "utf-8"))

    return work_dir + f"/{file_name}.pdf"

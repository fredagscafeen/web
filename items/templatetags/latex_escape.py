from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter(name="latex_escape")
@stringfilter
def latex_escape(value):
    """
    Escapes special characters in a string for use in LaTeX documents.
    """
    chars = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
        "\\": r"\textbackslash{}",
    }
    return "".join(chars.get(c, c) for c in value)

import re

from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

# From https://stackoverflow.com/questions/16259923/how-can-i-escape-latex-special-characters-inside-django-templates
def tex_escape(text):
    """
        :param text: a plain text message
        :return: the message escaped to appear correctly in LaTeX
    """
    conv = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\^{}",
        "\\": r"\textbackslash{}",
        "<": r"\textless{}",
        ">": r"\textgreater{}",
    }
    return "".join(conv.get(c, c) for c in text)


@register.filter
@stringfilter
def latex_trunc(value, width=r"\linewidth"):
    escaped_value = tex_escape(value)
    # return fr'\truncate{{{width}}}{{{escaped_value}}}'
    # \truncate breaks text too eagerly
    return fr"\clipbox{{0pt 0pt 0pt 0pt}}{{\parbox{{{width}}}{{\mbox{{{escaped_value}}}}}}}"

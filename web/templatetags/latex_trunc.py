from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
@stringfilter
def latex_trunc(value, width=r'\linewidth'):
	return fr'\truncate{{ {width} }}{{ {value} }}'

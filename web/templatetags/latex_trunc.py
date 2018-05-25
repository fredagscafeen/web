from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
@stringfilter
def latex_trunc(value, width=r'\linewidth'):
	underscore_escaped_value = value.replace('_', r'\_')
	#return fr'\truncate{{ {width} }}{{ {underscore_escaped_value} }}'
	# \truncate breaks text too eagerly
	return fr'\clipbox{{0pt 0pt 0pt 0pt}}{{\parbox{{ {width} }}{{ {underscore_escaped_value} }}}}'

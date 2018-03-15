from django.contrib import admin
from django.utils.translation import gettext_lazy as _


class NonNullFieldListFilter(admin.FieldListFilter):
    '''
    A field list filter with 3 choices:
    - All: Shows all
    - Yes: Only shows objects with non-null field
    - No: Only shows objects with null field
    '''
    def __init__(self, field, request, params, model, model_admin, field_path):
        self.lookup_kwarg = f'{field_path}__isnull'
        self.lookup_val = request.GET.get(self.lookup_kwarg)
        super().__init__(field, request, params, model, model_admin, field_path)
        if (self.used_parameters and self.lookup_kwarg in self.used_parameters and
            self.used_parameters[self.lookup_kwarg] in ('1', '0')):
            self.used_parameters[self.lookup_kwarg] = bool(int(self.used_parameters[self.lookup_kwarg]))

    def expected_parameters(self):
        return [self.lookup_kwarg]

    def choices(self, changelist):
        for lookup, title in (
                (None, _('All')),
                ('0', _('Yes')),
                ('1', _('No'))):
            yield {
                'selected': self.lookup_val == lookup,
                'query_string': changelist.get_query_string({self.lookup_kwarg: lookup}),
                'display': title,
            }

from django.apps import apps
from django.contrib import admin
from django.contrib.admin.options import csrf_protect_m


def custom_admin_view(app_label, name):
    def f(view_function):
        model_name = name.replace(" ", "_").lower()

        class FakeModelAdmin(admin.ModelAdmin):
            def __init__(self, model, admin_site):
                model._meta.concrete_model = FakeModel
                super().__init__(model, admin_site)

            @csrf_protect_m
            def changelist_view(self, *args, **kwargs):
                return view_function(self, *args, **kwargs)

            def has_add_permission(self, *args, **kwargs):
                return False

            def has_delete_permission(self, *args, **kwargs):
                return False

            def has_change_permission(self, *args, **kwargs):
                return False

        class FakeModel:
            class Meta:
                object_name = "FakeModel"
                concrete_model = None
                abstract = False
                swapped = False

                def get_ordered_objects(self):
                    return False

                def get_change_permission(self):
                    return f"change_{self.model_name}"

                @property
                def app_config(self):
                    return apps.get_app_config(self.app_label)

                @property
                def label(self):
                    return f"{self.app_label}.{self.object_name}"

                @property
                def label_lower(self):
                    return self.label

            _meta = Meta()
            _meta.app_label = app_label
            _meta.model_name = model_name
            _meta.module_name = model_name
            _meta.verbose_name_plural = name

        admin.site.register([FakeModel], FakeModelAdmin)

    return f

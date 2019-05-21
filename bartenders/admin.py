from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.utils.safestring import mark_safe
from django.http import HttpResponseRedirect
from django.urls import reverse

from django_object_actions import DjangoObjectActions

from bartenders.models import Bartender, BoardMember, BartenderApplication, BartenderShift, BoardMemberDepositShift, BoardMemberPeriod
from fredagscafeen.admin_filters import NonNullFieldListFilter

from .mailman2 import MailmanError

User = get_user_model()


@admin.register(Bartender)
class BartenderAdmin(DjangoObjectActions, admin.ModelAdmin):
    list_display = ('name', 'username', 'email')
    search_fields = ('name', 'username', 'email')
    list_filter = ('isActiveBartender', ('boardmember', NonNullFieldListFilter))

    change_actions = ('add_to_mailing_list', 'remove_from_mailing_list', 'create_admin_user')

    def add_to_mailing_list(self, request, obj):
        if not settings.MAILMAN_MUTABLE:
            messages.error(request, 'MAILMAN_MUTABLE is false!')
            return

        try:
            obj.add_to_mailing_list()
            messages.info(request, 'Successfully added to mailing list')
        except MailmanError as e:
            messages.error(request, f'Got Mailman error: {e}')

    add_to_mailing_list.label = 'Add to mailing list'

    def remove_from_mailing_list(self, request, obj):
        if not settings.MAILMAN_MUTABLE:
            messages.error(request, 'MAILMAN_MUTABLE is false!')
            return

        try:
            obj.remove_from_mailing_list()
            messages.info(request, 'Successfully removed from mailing list')
        except MailmanError as e:
            messages.error(request, f'Got Mailman error: {e}')


    remove_from_mailing_list.label = 'Remove from mailing list'

    def create_admin_user(self, request, obj):
        first_name, last_name = obj.name.rsplit(' ', maxsplit=1)
        user = User.objects.create(username=obj.username,
                                   email=obj.email,
                                   first_name=first_name,
                                   last_name=last_name)

        password = User.objects.make_random_password(length=30)
        user.set_password(password)

        user.is_staff = True
        user.save()

        messages.info(request, f'Created user {obj.username} with password {password}')

    create_admin_user.label = 'Create admin user'


@admin.register(BoardMember)
class BoardMemberAdmin(admin.ModelAdmin):
    list_display = ('thumbnail', 'bartender', 'title', 'period')
    list_display_links = ('thumbnail', 'bartender')
    list_select_related = ('bartender', )
    list_filter = ('period',)

    def thumbnail(self, obj):
        return mark_safe('<img src="%s" width="75px"/>' % obj.image.url) if obj.image else '<missing>'


@admin.register(BartenderApplication)
class BartenderApplicationAdmin(DjangoObjectActions, admin.ModelAdmin):
    list_display = ('name', 'created', 'username', 'email')

    change_actions = ('accept', 'deny')

    def accept(self, request, obj):
        pk = obj.accept()
        obj.delete()
        return HttpResponseRedirect(reverse('admin:bartenders_bartender_change', args=(pk, )))

    def deny(self, request, obj):
        obj.delete()
        return HttpResponseRedirect(reverse('admin:bartenders_bartenderapplication_changelist'))


@admin.register(BartenderShift)
class BartenderShiftAdmin(admin.ModelAdmin):
    list_display = ('start_datetime', 'shift_responsible', 'other_bartenders_list')
    filter_horizontal = ('other_bartenders',)

    def shift_responsible(self, obj):
        return obj.responsible.name

    def other_bartenders_list(self, obj):
        return ", ".join([s.name for s in obj.other_bartenders.all()])

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'responsible':
            kwargs['queryset'] = Bartender.shift_ordered()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(BoardMemberDepositShift)
class BoardMemberDepositShiftAdmin(admin.ModelAdmin):
    list_display = ('start_date', 'end_date', 'responsible_board_members')
    filter_horizontal = ('responsibles',)

    def responsible_board_members(self, obj):
        return ", ".join([s.name for s in obj.responsibles.all()])

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'responsibles':
            kwargs['queryset'] = Bartender.shift_ordered()

        return super().formfield_for_manytomany(db_field, request, **kwargs)


class BoardMemberInline(admin.StackedInline):
    model = BoardMember


@admin.register(BoardMemberPeriod)
class BoardMemberPeriodAdmin(admin.ModelAdmin):
    inlines = [
        BoardMemberInline
    ]

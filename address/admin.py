from django.contrib import admin

from .models import Address


class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'first_name', 'last_name', 'phone', 'email',
                    'city', 'state', 'pin_code',  'updated_at', "is_active",)

    list_display_links = ('user', 'first_name', 'last_name')

    readonly_fields = ('updated_at',)

    # In 'user__username', 'user' (ForeignKey) refers to an Account class object and '__username' is its ForeignKey attribute.
    search_fields = ['user__email', 'first_name', 'last_name', 'phone', 'email',
                     'city', 'state', 'pin_code',]

    # ordering = ('-date_joined',) descending order
    # In 'user__username', 'user' (ForeignKey) refers to an Account class object and '__username' is its ForeignKey attribute.
    list_filter = ("is_active",)


# Register your models here.
admin.site.register(Address, AddressAdmin)

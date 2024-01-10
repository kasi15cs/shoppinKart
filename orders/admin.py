from django.contrib import admin

from .models import Payment, Order, OrderProduct

# Register your models here.


class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    extra = 0

    readonly_fields = ('payment', 'user', 'product',
                       'quantity', 'variations', 'product_price', 'product_total_price', 'ordered')


class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'order_number', 'payment', 'city',
                    'order_total', 'status', 'ip', "is_ordered", 'updated_at')

    list_display_links = ('user', 'order_number')

    readonly_fields = ('updated_at',)

    search_fields = ['user__email', 'first_name', 'last_name', 'phone', 'email',
                     'city', 'state', 'pin_code', 'order_number']

    list_filter = ("is_ordered", 'status')
    list_per_page = 20

    inlines = [OrderProductInline]


class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'payment_id', 'payment_method',
                    'amount_paid', 'status', 'created_at')

    list_display_links = ('user', 'payment_id')

    search_fields = ['user__email', 'payment_id']

    list_filter = ("payment_method", 'status',)


admin.site.register(Payment, PaymentAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderProduct)

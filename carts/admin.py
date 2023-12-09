from django.contrib import admin

from .models import Cart, CartItem

# Register your models here.


class CartAdmin(admin.ModelAdmin):
    list_display = ("cart_id", "date_added")


class CartItemAdmin(admin.ModelAdmin):
    list_display = ("product", "cart", "get_variations",
                    "quantity", 'user', "is_active")

    def get_variations(self, instance):
        return [variation for variation in instance.variations.all()]


admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)

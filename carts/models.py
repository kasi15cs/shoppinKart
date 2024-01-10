from django.db import models
from accounts.models import Account

from store.models import Product, Variation

# Create your models here.


class Cart(models.Model):
    cart_id = models.CharField(max_length=250, blank=True)
    date_added = models.DateField(auto_now_add=True)

    def __str__(self) -> str:
        return self.cart_id


class CartItem(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variations = models.ManyToManyField(Variation, blank=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null=True)
    quantity = models.IntegerField()
    is_active = models.BooleanField(default=True)

    def ProductCount(self):
        productCount = 0
        cart_items = CartItem.objects.filter(product=self.product)

        for cart_item in cart_items:
            productCount += cart_item.quantity

        return productCount
    

    def subTotal(self):
        return self.product.price * self.quantity

    def __unicode__(self) -> str:
        return self.product

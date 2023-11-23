from carts.models import Cart, CartItem
from store.models import Product

from django.shortcuts import render


def home(request, cart_quantities=0):
    product = Product.objects.all().filter(is_available=True)
    context = {
        'products': product,
    }
    return render(request, 'home.html', context)

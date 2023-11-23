

from carts.models import Cart, CartItem
from carts.views import _cart_id
from .models import Category


def menu_links(request, cart_quantities=0):

    links = Category.objects.all()
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))

        cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        for cart_item in cart_items:
            cart_quantities += cart_item.quantity

        context = dict(links=links, cart_quantities=cart_quantities)
    except Cart.DoesNotExist:
        context = dict(links=links)
    return context

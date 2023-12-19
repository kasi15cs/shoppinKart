from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
import requests

from address.models import Address
from .models import Cart, CartItem

from store.models import Product, Variation
from django.core.exceptions import ObjectDoesNotExist

from django.contrib.auth.decorators import login_required


def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart


########################### Plus button functionality of cart and "Add to cart" button of the product detail page #############################


def add_cart(request, product_id):
    current_user = request.user
    product = Product.objects.get(id=product_id)

    product_variation = []
    if request.method == 'POST':
        for item in request.POST:
            key = item
            value = request.POST[key]

            try:
                # The iexact lookup is used to get records with a specified value. The iexact lookup is case insensitive.
                variation = Variation.objects.get(
                    product=product, variation_category__iexact=key, variation_value__iexact=value)

                product_variation.append(variation)

            except:
                pass

    # if the user is authenticated
    if current_user.is_authenticated:

        is_cartItem_exits_for_given_user = CartItem.objects.filter(
            user=current_user).exists()

        if is_cartItem_exits_for_given_user:
            cart = CartItem.objects.filter(user=current_user)[0].cart
        else:
            cart = Cart.objects.create(cart_id=_cart_id(request))
            cart.save()

        is_given_cart_item_exits = CartItem.objects.filter(
            product=product, user=current_user).exists()
        ex_var_list = []
        id = []

        if is_given_cart_item_exits:

            cart_item = CartItem.objects.filter(
                product=product, user=current_user, cart=cart)

            for item in cart_item:
                existing_variation = item.variations.all()
                ex_var_list.append(list(existing_variation))
                id.append(item.id)

            if product_variation in ex_var_list:
                # increase the cart item quantity
                index = ex_var_list.index(product_variation)
                item_id = id[index]
                item = CartItem.objects.get(id=item_id)
                item.quantity += 1
                # item.save()
            else:
                item = CartItem.objects.create(
                    product=product, quantity=1, user=current_user, cart=cart)
                if len(product_variation) > 0:
                    # item.variations.clear()
                    item.variations.add(*product_variation)

        else:
            item = CartItem.objects.create(
                product=product,
                quantity=1,
                user=current_user,
                cart=cart,
            )
            if len(product_variation) > 0:
                item.variations.clear()
                item.variations.add(*product_variation)

        # item.save()
        # return redirect('cart')

    else:
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
        except Cart.DoesNotExist:
            cart = Cart.objects.create(cart_id=_cart_id(request))
            cart.save()

        is_given_cart_item_exits = CartItem.objects.filter(
            product=product, cart=cart).exists()

        ex_var_list = []
        id = []
        if is_given_cart_item_exits:
            cart_item = CartItem.objects.filter(product=product, cart=cart)
            # existing_variations -> database
            # current_variation -> product_variation
            # item_id -> database

            for item in cart_item:
                existing_variation = item.variations.all()
                ex_var_list.append(list(existing_variation))
                id.append(item.id)

            if product_variation in ex_var_list:
                # increase the cart item quantity
                index = ex_var_list.index(product_variation)
                item_id = id[index]
                item = CartItem.objects.get(product=product, id=item_id)
                item.quantity += 1
                # item.save()
            else:
                item = CartItem.objects.create(
                    product=product, quantity=1, cart=cart)
                if len(product_variation) > 0:
                    # item.variations.clear()
                    item.variations.add(*product_variation)

        else:
            item = CartItem.objects.create(
                product=product, cart=cart, quantity=1,)
            if len(product_variation) > 0:
                item.variations.clear()
                item.variations.add(*product_variation)

    item.save()

    return redirect('cart')


############################ Minus button functionality of cart #############################

def remove_cart(request, cart_item_id):

    if request.user.is_authenticated:
        current_user = request.user
        cart = CartItem.objects.filter(user=current_user)[0].cart
        cart_item = CartItem.objects.get(user=current_user, id=cart_item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()

        is_cartItem_exits_for_given_user = CartItem.objects.filter(
            user=current_user).exists()

        if is_cartItem_exits_for_given_user == False:
            cart.delete()

    else:

        cart = Cart.objects.get(cart_id=_cart_id(request))

        cart_item = CartItem.objects.get(id=cart_item_id)

        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()

        is_cartItem_exits = CartItem.objects.filter(cart=cart).exists()

        if is_cartItem_exits == False:
            cart.delete()

    return redirect('cart')


# ############################ remove button funtionality of cart ########################################

def remove_cart_items(request, cart_item_id):

    if request.user.is_authenticated:
        current_user = request.user
        cart = CartItem.objects.filter(user=current_user)[0].cart
        cart_item = CartItem.objects.get(user=current_user, id=cart_item_id)
        cart_item.delete()
        is_cartItem_exits_for_given_user = CartItem.objects.filter(
            user=current_user).exists()

        if is_cartItem_exits_for_given_user == False:
            cart.delete()

    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = CartItem.objects.get(cart=cart, id=cart_item_id)

        cart_item.delete()
        is_cartItem_exits = CartItem.objects.filter(cart=cart).exists()

        if is_cartItem_exits == False:
            cart.delete()

    return redirect('cart')


#################################### Calculating the bills of Cart Items #############################

def cart(request, total=0, tax=0, grand_total=0, quantity=0, cart_items=None):
    address = None
    active_address = None

    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(
                user=request.user, is_active=True)

            address = Address.objects.filter(user=request.user)
            active_address = Address.objects.get(
                user=request.user, is_active=True)

        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        tax = (2*total)/100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass
    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
        'address': address,
        'active_address': active_address,
    }
    return render(request, 'store/cart.html', context)


#################################### Checkout button functionality #############################

@login_required(login_url='login')
def checkout(request, total=0, quantity=0, cart_items=None):
    current_user = request.user
    default_address = None
    address = None
    try:
        tax = 0
        grand_total = 0
        if current_user.is_authenticated:
            cart_items = CartItem.objects.filter(
                user=request.user, is_active=True)

            default_address = Address.objects.get(
                user=current_user, is_active=True)

            address = Address.objects.filter(user=current_user)

        if len(cart_items) <= 0:
            return redirect("store")

        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity

        tax = (2*total)/100
        grand_total = total + tax

    except ObjectDoesNotExist:
        pass
    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
        'default_address': default_address,
        'address': address,

    }
    return render(request, 'orders/checkout.html', context)


#################################### change button functionality #############################

def billing_address(request, billing_address_id):
    current_user = request.user
    if current_user.is_authenticated:
        active_address = Address.objects.get(user=current_user, is_active=True)

        if active_address.id != billing_address_id:
            active_address.is_active = False
            active_address.save()
            active_address = Address.objects.get(id=billing_address_id)
            active_address.is_active = True
            active_address.save()

        url = request.META.get('HTTP_REFERER')
        try:
            # '/cart/checkout/' OR /cart/ contain by query
            path = requests.utils.urlparse(url).path

            if '/cart/checkout/' == path:
                return redirect('checkout')
            else:
                return redirect('cart')
        except:
            pass

    return redirect('cart')

import time
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
import requests
from address.models import Address

from carts.models import CartItem
from store.models import Product
from .models import Order, OrderProduct, Payment
import uuid
from django.contrib.sessions.models import Session

# paypal import
import paypalrestsdk
from django.conf import settings
from django.urls import reverse

# email
from django.template.loader import render_to_string
from django.core.mail import EmailMessage


def create_payment(request):
    paypalrestsdk.configure({
        "mode": "sandbox",  # Change to "live" for production
        "client_id": settings.PAYPAL_CLIENT_ID,
        "client_secret": settings.PAYPAL_SECRET,
    })

    payment_method = request.session['context']['payment_method']
    order_number = request.session['context']['order_number']
    grand_total = str(request.session['context']['grand_total'])

    if request.session['context']['payment_method'] == 'paypal':

        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": payment_method,
            },
            "redirect_urls": {
                "return_url": request.build_absolute_uri(reverse('execute_payment')),
                # request.build_absolute_uri(reverse('payment_failed')),
                "cancel_url": request.build_absolute_uri(reverse('payment_failed'))
            },
            "transactions": [
                {
                    "amount": {
                        "total": grand_total,
                        "currency": "USD",
                    },

                    "description": "This is the payment transaction description."
                }
            ]
        })
        if payment.create():
            # Redirect the user to given approval url
            approval_url = payment.links[1].href
            return redirect(approval_url)
        else:
            # print(payment.error)
            return HttpResponse("failed")


def execute_payment(request):
    payment_id = request.GET.get('paymentId')
    payer_id = request.GET.get('PayerID')

    request.session["payment_id"] = payment_id

    payment_approval = paypalrestsdk.Payment.find(payment_id)

    if payment_approval.execute({"payer_id": payer_id}):

        # payment state created (i.e status completed)
        request.session["status"] = "Completed"

        return redirect('order_successful')
    else:
        print(payment_approval.error)


def payment_failed(request):

    return render(request, 'payment/payment_failed.html')


def order_successful(request):
    current_user = request.user

    payment_id = request.session["payment_id"]
    payment_method = request.session['context']['payment_method']
    amount_paid = request.session['context']['grand_total']
    order_number = request.session['context']['order_number']
    status = request.session['status']

   # store transaction details inside payment model
    payment = Payment.objects.create(
        user=current_user,
        payment_id=payment_id,
        payment_method=payment_method,
        amount_paid=amount_paid,
        status=status
    )

    # Updating the order table
    order = Order.objects.get(
        user=current_user, is_ordered=False, order_number=order_number)
    order.is_ordered = True
    order.payment = payment
    order.save()

    # Move the cart items to OrderProduct table
    cart_items = CartItem.objects.filter(user=current_user)

    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order = order
        orderproduct.payment = payment
        orderproduct.user = current_user
        orderproduct.product = item.product
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.product_total_price = item.quantity*item.product.price
        orderproduct.ordered = True
        orderproduct.save()

        # setting variations of product
        orderproduct.variations.set(item.variations.all())
        orderproduct.save()

        # reduce the quantity of the sold products
        product = Product.objects.get(id=item.product.id)
        product.stock -= item.quantity
        if product.stock <= 0:
            product.is_available = False
        product.save()

    # clearing the cart-items by deleting the cart
    try:
        cart_id = cart_items[0].cart
        cart_id.delete()
    except:
        pass

    # send order recieved email to customer
    ordered_products = OrderProduct.objects.filter(
        user=current_user, order=order)
    subtotal = 0
    for item in ordered_products:
        subtotal += item.product_total_price

    mail_subject = "Thank you for your order"
    message = render_to_string('orders/order_recieved_email.html', {
        'user': current_user,
        'order': order,
        'ordered_products': ordered_products,
        'order_number': order.order_number,
        'transID': payment.payment_id,
        'payment': payment,
        'subtotal': subtotal,

    })

    to_email = request.user.email
    send_email = EmailMessage(mail_subject, message, to=[to_email])
    send_email.send()

    order_completed_url = str(request.build_absolute_uri(reverse(
        "order_completed")))+"?order_number="+order_number+"&payment_id="+payment_id
    # render(request, 'orders/order_complete.html')
    return redirect(order_completed_url)


def place_order(request):
    current_user = request.user
    quantity = 0
    if current_user.is_authenticated:
        # if the cart is empty, then redirect back to shop page
        cart_items = CartItem.objects.filter(user=current_user)
        cart_count = cart_items.count()

        if cart_count <= 0:
            return redirect('store')

        total = 0
        tax = 0

        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        tax = (2*total)/100
        grand_total = total + tax

        address = Address.objects.get(user=current_user, is_active=True)

        # print(uuid.uuid4())
        if request.method == "POST":

            payment_method = request.POST['payment_method']
            order_note = request.POST['order_note']
            order_number = str(int(time.time()))
            ip = request.META.get('REMOTE_ADDR')
            order = Order()

            order.user = current_user
            order.order_number = order_number
            order.first_name = address.first_name
            order.last_name = address.last_name
            order.phone = address.phone
            order.email = address.email
            order.address_line_1 = address.address_line_1
            order.address_line_2 = address.address_line_2
            order.pin_code = address.pin_code
            order.city = address.city
            order.state = address.state
            order.country = address.country
            order.order_note = order_note
            order.order_total = grand_total
            order.tax = tax
            order.ip = ip
            order.save()

            context = {
                'order_number': order_number,
                'grand_total': grand_total,
                'payment_method': payment_method,
            }

            request.session["context"] = context

    return redirect("create_payment")


def order_completed(request):

    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)
        payment = Payment.objects.get(payment_id=transID)

        subtotal = 0
        for item in ordered_products:
            subtotal += item.product_total_price
        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID': payment.payment_id,
            'payment': payment,
            'subtotal': subtotal,
        }

        return render(request, "orders/order_complete.html", context)

    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')


#####################################
# "item_list": {
#     "items": [
#         {
#             "name": "tshirt",
#             "sku": "product011",
#             "price": "612.00",
#             "currency": "USD",
#             "quantity": 1
#         }
#     ]
# },
############################################
# delete session key and value
# del request.session['complete_pending']
# all session key and value
# for key in request.session.keys():
#     print(key, "=", request.session[key])

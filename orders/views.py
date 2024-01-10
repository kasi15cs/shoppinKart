import time
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
import razorpay
import requests
from address.models import Address

from carts.models import CartItem
from store.models import Product
from .models import Order, OrderProduct, Payment
import uuid
from django.contrib.sessions.models import Session
from django.contrib.auth.decorators import login_required


# settings of django project file
from django.conf import settings

# paypal import
import paypalrestsdk
from django.urls import reverse

# email
from django.template.loader import render_to_string
from django.core.mail import EmailMessage

from django.contrib import messages

import json


def order_successful(request):
    current_user = request.user

    payment_id = request.GET.get('payment_id')
    order_number = request.GET.get('order_number')

    # store transaction details inside payment model
    payment = Payment.objects.get(user=current_user, payment_id=payment_id)

    # order table
    order = Order.objects.get(
        user=current_user, order_number=order_number)

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

    # url
    order_completed_url = str(request.build_absolute_uri(reverse(
        "order_completed")))+"?order_number="+order_number+"&payment_id="+payment_id

    return redirect(order_completed_url)


def order_completed(request):

    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')
    total_discount = 0

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)
        payment = Payment.objects.get(payment_id=transID)

        subtotal = 0
        for item in ordered_products:
            sub_total = item.product_total_price
            subtotal += sub_total
            discount = item.product.discount
            total_discount += round(sub_total*(discount/(100-discount)))

        subtotal_withDisc = total_discount + subtotal
        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID': payment.payment_id,
            'payment': payment,
            'subtotal': subtotal,
            'total_discount': total_discount,
            'subtotal_withDisc': subtotal_withDisc,
        }

        return render(request, "orders/order_complete.html", context)

    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')


# Placing Orders
@login_required(login_url='login')
def place_order(request):
    current_user = request.user
    quantity = 0
    razorpay_body = None
    try:
        razorpay_body = json.loads(request.body)
    except:
        pass

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

        # delivery Address
        address = Address.objects.get(user=current_user, is_active=True)

        # Creating new Order object for storing
        order = Order()

        # print(uuid.uuid4())
        if request.method == "POST" and razorpay_body == None:
            payment_method = "paypal"
            order_note = request.POST['order_note']
            order_number = str(int(time.time()))
        else:
            payment_method = razorpay_body['payment_method']
            order_note = razorpay_body['order_note']
            order_number = razorpay_body['orderID']
            payment_id = razorpay_body['transID']

            payment = Payment.objects.create(
                user=current_user,
                payment_id=payment_id,
                payment_method=payment_method,
                amount_paid=grand_total,
                status="Completed",
            )

            order.payment = payment
            order.is_ordered = True
            order.status = "Accepted"

        ip = request.META.get('REMOTE_ADDR')

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

        if request.method == "POST" and razorpay_body != None:
            data = {
                'order_number': order_number,
                'payment_id': payment_id,
            }
            return JsonResponse(data)

        elif request.method == "POST" and razorpay_body == None:

            create_pay_url = str(request.build_absolute_uri(reverse(
                'create_payment')))+"?order_number="+order_number
            return redirect(create_pay_url)

    return redirect('login')


def create_payment(request):

    current_user = request.user
    payment_method = "paypal"
    order_number = request.GET.get("order_number")
    grand_total = Order.objects.get(
        order_number=order_number, user=current_user).order_total

    if payment_method == 'paypal':
        paypalrestsdk.configure({
            "mode": "sandbox",  # Change to "live" for production
            "client_id": settings.PAYPAL_CLIENT_ID,
            "client_secret": settings.PAYPAL_SECRET,
        })

        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": payment_method,
            },
            "redirect_urls": {
                "return_url": request.build_absolute_uri(reverse('execute_payment'))+"?order_number="+order_number,
                # request.build_absolute_uri(reverse('payment_failed')),
                "cancel_url": request.build_absolute_uri(reverse('payment_failed'))+"?order_number="+order_number+"&payment_method="+payment_method,
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
        try:
            if payment.create():
                # Redirect the user to given approval url
                approval_url = payment.links[1].href
                return redirect(approval_url)
            else:
                return HttpResponse("failed")
        except:
            print("\n\n\npass1\n\n\n")


def execute_payment(request):
    # try:
    current_user = request.user

    payment_id = request.GET.get('paymentId')
    payer_id = request.GET.get('PayerID')

    # payment_method
    payment_method = "payal"

    # Order
    order_number = request.GET.get('order_number')
    order = Order.objects.get(order_number=order_number, user=current_user)
    amount_paid = order.order_total

    # payment_approval from paypal
    payment_approval = paypalrestsdk.Payment.find(payment_id)

    # store transaction details inside payment model
    payment = Payment.objects.create(
        user=current_user,
        payment_id=payment_id,
        payment_method=payment_method,
        amount_paid=amount_paid,
    )

    # Updating the order table
    order = Order.objects.get(
        user=current_user, is_ordered=False, order_number=order_number)
    order.payment = payment

    if payment_approval.execute({"payer_id": payer_id}):

        payment.status = "Completed"
        payment.save()

        order.is_ordered = True
        order.status = 'Accepted'
        order.save()

        order_successful_url = str(request.build_absolute_uri(reverse(
            "order_successful"))) + "?order_number="+order_number+"&payment_id="+payment_id
        return redirect(order_successful_url)
    else:
        payment.status = "Failed"
        payment.save()

        order.status = 'Failed'

        order.save()

        messages.error(request, "Payment Failed!!")
        return redirect('checkout')


def payment_failed(request):

    current_user = request.user

    order_number = request.GET.get('order_number')
    payment_method = request.GET.get('payment_method')
    try:
        razorpay_body = json.loads(request.body)
        payment_method = razorpay_body['payment_method']
        order_note = razorpay_body['order_note']
        order_number = razorpay_body['orderID']
        payment_id = razorpay_body['transID']
        amount_paid = razorpay_body['grand_total']
        tax = razorpay_body['tax']

    except:
        pass

    if payment_method == 'razorpay':

        order_note = request.GET.get('order_note')
        order_number = razorpay_body['orderID']
        payment_id = razorpay_body['transID']
        amount_paid = razorpay_body['grand_total']
        tax = razorpay_body['tax']

        payment = Payment.objects.create(
            user=current_user,
            payment_method=payment_method,
            amount_paid=amount_paid,
            payment_id=payment_id,
            status="Failed"
        )
        # delivery Address
        address = Address.objects.get(user=current_user, is_active=True)

        # ip addresss
        ip = request.META.get('REMOTE_ADDR')

        # Creating new Order object for storing
        order = Order()
        order.user = current_user
        order.payment = payment
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
        order.order_total = amount_paid
        order.is_ordered = False
        order.tax = tax
        order.ip = ip
        order.status = "Failed"
        order.save()

        data = {
            'order_number': order_number,
            'payment_id': payment_id,
        }
        messages.error(request, "Payment Failed!!")
        return JsonResponse(data)

    elif payment_method == "paypal":

        amount_paid = Order.objects.get(
            order_number=order_number, user=current_user).order_total

        # store transaction details inside payment model
        payment = Payment.objects.create(
            user=current_user,
            payment_method=payment_method,
            amount_paid=amount_paid,
            status="Failed"
        )

        # Updating the order table
        order = Order.objects.get(
            user=current_user, is_ordered=False, order_number=order_number)
        order.status = 'Failed'
        order.payment = payment
        order.save()
    messages.error(
        request, "Payment Failed!!")
    return redirect('checkout')

############################################
# delete session key and value
# del request.session['complete_pending']
# all session key and value
# for key in request.session.keys():
#     print(key, "=", request.session[key])

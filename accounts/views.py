from django.contrib import messages, auth
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from carts.models import Cart, CartItem
from carts.views import _cart_id
from orders.models import Order, OrderProduct
from .forms import RegistrationForm, UserForm, UserProfileForm
from .models import Account, UserProfile
from django.contrib.auth.decorators import login_required

# verification email
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage


import requests


def register(request):

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            phone_number = form.cleaned_data['phone_number']
            password = form.cleaned_data['password']

            username = email.split('@')[0]
            user = Account.objects.create_user(
                first_name=first_name, last_name=last_name, username=username, email=email, password=password)

            user.phone_number = phone_number

            user.save()

            # Create User Profile
            profile = UserProfile()
            profile.user_id = user.id
            profile.profile_picture = "default/default_avatar.jpg"
            profile.save()

            # USER ACTIVATION
            current_site = get_current_site(request)
            mail_subject = "Please activate your account"
            message = render_to_string('accounts/account_verification_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })

            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            # messages.success(request, "Registration Successful.")

            # encode_email = urlsafe_base64_encode(force_bytes(email))

            return redirect("/accounts/login/?command=verification&email="+email)
    else:
        form = RegistrationForm()

    context = {
        'form': form,
    }
    return render(request, "accounts/register.html", context)


def login(request):

    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(email=email, password=password)

        if user is not None:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exits = CartItem.objects.filter(
                    cart=cart).exists()

                if is_cart_item_exits:

                    cart_item = CartItem.objects.filter(cart=cart)
                    is_cartItem_exits_for_given_user = CartItem.objects.filter(
                        user=user).exists()

                    if is_cartItem_exits_for_given_user:
                        variation_item_check = list()
                        cartItem_id = list()
                        cart_id = CartItem.objects.filter(user=user)[0].cart
                        cart_item_of_user = CartItem.objects.filter(
                            cart=cart_id)

                        for item in cart_item_of_user:
                            variation_list_of_user = [item.product.pk]
                            vary = [var for var in item.variations.all()]

                            variation_list_of_user.append(vary)
                            variation_item_check.append(variation_list_of_user)

                            cartItem_id.append(item.id)

                        for item in cart_item:
                            variation_list = [item.product.pk]
                            vary = [var for var in item.variations.all()]

                            variation_list.append(vary)

                            if variation_list in variation_item_check:

                                # updating cartItem quantities of login user
                                index = variation_item_check.index(
                                    variation_list)
                                item_id = cartItem_id[index]

                                updated_item = CartItem.objects.get(id=item_id)

                                updated_item.quantity += item.quantity
                                updated_item.save()

                            else:

                                updated_item = CartItem.objects.create(
                                    product=item.product, quantity=item.quantity, cart=cart_id, user=user)
                                if len(variation_list[1]) > 0:
                                    updated_item.variations.add(
                                        *variation_list[1])

                        cart_item.delete()
                        cart.delete()

                    else:
                        for item in cart_item:
                            item.user = user
                            item.save()

            except:
                pass

            auth.login(request, user)
            messages.success(request, 'You are logged in.')

            # 'http://127.0.0.1:8000/accounts/login/?next=/cart/checkout/' contain by URL
            url = request.META.get('HTTP_REFERER')
            try:
                # 'next=/cart/checkout/' contain by query
                query = requests.utils.urlparse(url).query

                # next=/cart/checkout/
                # 'query.split("&")' any symbol we can pass but make sure that it is not present in that query
                params = dict(x.split('=') for x in query.split("&"))

                if "next" in params:
                    nextPage = params['next']
                    return redirect(nextPage)

            except:
                return redirect('home')

        else:
            messages.error(request, "Invaild login credential.")
            return redirect('login')

    return render(request, "accounts/login.html")


@login_required(login_url='login')
def logout(request):
    auth.logout(request)
    messages.success(request, 'You are Logged out.')
    return redirect('login')


# user activation functionality

def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Congretulation! Your account is activated.")
        return redirect('login')
    else:
        messages.error(request, 'Invalid activation link.')
    return redirect('register')


# Dashboard functionality

@login_required(login_url='login')
def dashboard(request):
    current_user = request.user
    userprofile = get_object_or_404(UserProfile, user=current_user)
    orders = Order.objects.filter(
        user=current_user, is_ordered=True).order_by("-created_at")

    orders_count = orders.count()
    # orders_count = len(orders)
    context = {
        'orders_count': orders_count,
        'userprofile': userprofile,
    }
    return render(request, 'accounts/dashboard.html', context)


# forgotPassword button functionality

def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST['email']

        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__exact=email)

            # Reset password email
            current_site = get_current_site(request)
            mail_subject = "Reset Your Password"
            message = render_to_string('accounts/reset_password_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })

            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            messages.success(
                request, "Password reset email has been sent to your email address. ")

            return redirect('login')
        else:

            messages.error(request, "Account does not exist!")
            return redirect('forgotPassword')

    return render(request, 'accounts/forgotPassword.html')


# forgot password validation

def resetpassword_validate(request, uidb64, token):

    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, 'Please reset your password.')
        return redirect('resetPassword')

    else:

        messages.error(request, "This link has been expired!")

    return render(request, 'accounts/login.html')


# Reset page for setting new password

def resetPassword(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            uid = request.session.get('uid')

            user = Account.objects.get(pk=uid)

            user.set_password(password)
            user.save()

            messages.success(request, "Password reset successful")

            return redirect('login')
        else:
            messages.error(request, "Password do not match!")
            return redirect("resetPassword")
    return render(request, 'accounts/resetPassword.html')


# my_orders button (in Dashboard) functionality
@login_required(login_url='login')
def my_orders(request):
    current_user = request.user
    orders = Order.objects.filter(
        user_id=current_user.id, is_ordered=True).order_by("-created_at")
    context = {
        'orders': orders,
    }
    return render(request, "accounts/my_orders.html", context)


# EditProfile functionality in dashboard
@login_required(login_url='login')
def edit_profile(request):
    current_user = request.user
    userprofile = get_object_or_404(UserProfile, user=current_user)

    if request.method == "POST":
        user_form = UserForm(request.POST, instance=current_user)
        profile_form = UserProfileForm(
            request.POST, request.FILES, instance=userprofile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect('edit_profile')
    else:
        user_form = UserForm(instance=current_user)
        profile_form = UserProfileForm(instance=userprofile)

    context = {
        "user_form": user_form,
        "profile_form": profile_form,
        "userprofile": userprofile,
    }
    return render(request, "accounts/edit_profile.html", context)


# ChangePassword functionality in Dashboard tab
@login_required(login_url='login')
def change_password(request):
    current_user = request.user
    if request.method == "POST":
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        user = Account.objects.get(username__exact=current_user.username)

        if new_password == confirm_password:
            success = user.check_password(current_password)
            if success:
                user.set_password(new_password)
                user.save()

                messages.success(request, "Password updated successfully.")
                return redirect('dashboard')
            else:
                messages.error(
                    request, "Please enter valid current password")
                return redirect('change_password')
        else:
            messages.error(request, "Password does not match.")
            return redirect('change_password')

    return render(request, "accounts/change_password.html")

#


@login_required(login_url='login')
def order_detail(request, order_id):
    order_detail = OrderProduct.objects.filter(order__order_number=order_id)
    order = Order.objects.get(order_number=order_id)

    total_discount = 0
    subtotal = 0
    for item in order_detail:
        sub_total = item.product_total_price
        subtotal += sub_total
        discount = item.product.discount
        total_discount += round(sub_total*(discount/(100-discount)))

        subtotal_withDisc = sub_total+total_discount

    context = {
        'order': order,
        'order_detail': order_detail,
        'subtotal_withDisc': subtotal_withDisc,
        'total_discount': total_discount,
    }
    return render(request, 'accounts/order_detail.html', context)

from django.http import HttpResponse
from django.shortcuts import redirect, render

from .forms import AddressForm

from .models import Address

# Create your views here.


def manage_address(request):

    current_user = request.user

    if current_user.is_authenticated:
        address = Address.objects.filter(user=current_user)

    context = {
        'address': address,
    }

    return render(request, 'address/addressess.html', context)


def delete_address(request, address_id):
    current_user = request.user
    if current_user.is_authenticated:
        address = Address.objects.get(id=address_id)
        if address.is_active == True:
            new_active_address = Address.objects.filter(user=current_user)
            for nw_atv_add in new_active_address:
                if nw_atv_add.id != address.id:
                    nw_atv_add.is_active = True
                    nw_atv_add.save()
                    break

        address.delete()

    return redirect('manage_address')


def add_address(request):
    current_user = request.user
    if current_user.is_authenticated:

        if request.method == "POST":
            form = AddressForm(request.POST)
            if form.is_valid():

                address = Address()
                address.user = current_user
                address.first_name = form.cleaned_data['first_name'].capitalize(
                )
                address.last_name = form.cleaned_data['last_name'].capitalize()
                address.phone = form.cleaned_data['phone']
                address.email = form.cleaned_data['email']
                address.address_line_1 = form.cleaned_data['address_line_1']
                address.address_line_2 = form.cleaned_data['address_line_2']
                address.country = form.cleaned_data['country'].capitalize()
                address.state = form.cleaned_data['state'].capitalize()
                address.city = form.cleaned_data['city'].capitalize()
                address.pin_code = form.cleaned_data['pin_code']

                is_address_exits = Address.objects.filter(
                    user=current_user).exists()
                if is_address_exits:
                    address.save()
                else:
                    address.is_active = True
                    address.save()
            return redirect('manage_address')

        else:
            return render(request, 'address/add_address.html')


def edit_address(request, address_id):
    current_user = request.user

    if current_user.is_authenticated:
        if request.method == "POST":
            form = AddressForm(request.POST)
            if form.is_valid():
                # Store all the billing information inside order table

                address = Address.objects.get(id=address_id)
                address.user = current_user
                address.first_name = form.cleaned_data['first_name']
                address.last_name = form.cleaned_data['last_name']
                address.phone = form.cleaned_data['phone']
                address.email = form.cleaned_data['email']
                address.address_line_1 = form.cleaned_data['address_line_1']
                address.address_line_2 = form.cleaned_data['address_line_2']
                address.country = form.cleaned_data['country']
                address.state = form.cleaned_data['state']
                address.city = form.cleaned_data['city']
                address.pin_code = form.cleaned_data['pin_code']
                address.save()
            return redirect('manage_address')

        else:
            address = Address.objects.get(id=address_id)

            context = {
                'address': address,
            }

            return render(request, 'address/edit_address.html', context)

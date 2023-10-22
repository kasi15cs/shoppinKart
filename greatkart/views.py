from store.models import Product

from django.shortcuts import render


def home(request):
    product = Product.objects.all().filter(is_available=True)

    context = {
        'products': product,
    }
    return render(request, 'home.html', context)

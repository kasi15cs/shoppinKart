from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from carts.models import CartItem
from carts.views import _cart_id

from django.contrib import messages

from category.models import Category

from django.db.models import Q

from orders.models import OrderProduct

from .forms import ReviewForm

from .models import Product, ReviewRating

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.contrib.auth.decorators import login_required

from statistics import mean
from math import floor, ceil


# Create your views here.


def store(request, category_slug=None):

    categories = None
    products = None

    if category_slug != None:
        categories = get_object_or_404(Category, slug=category_slug)

        products = Product.objects.filter(
            category=categories, is_available=True).order_by('id')

    else:
        products = Product.objects.all().filter(is_available=True).order_by('id')

    product_count = products.count()
    paginator = Paginator(products, 6)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)

    context = {
        'products': paged_products,
        'product_count': product_count,
        'category_slug': category_slug,

    }
    return render(request, 'store/store.html', context)


# Product details page
def product_detail(request, category_slug, product_slug):

    current_user = request.user
    reviews = None
    try:

        single_product = Product.objects.get(
            category__slug=category_slug, slug=product_slug)

        in_cart = CartItem.objects.filter(
            cart__cart_id=_cart_id(request), product=single_product).exists()

    except Exception as e:
        raise e

    if current_user.is_authenticated:
        orderproduct_check = OrderProduct.objects.filter(
            user=request.user, product=single_product).exists()
    else:
        orderproduct_check = None

    # Get all reviews regarding this product

    reviews = ReviewRating.objects.filter(product=single_product, status=True)

    # Average of review-rating
    avg_rating = mean([rv.rating for rv in reviews])
    floor_avg_rating = floor(avg_rating)
    ceil_avg_rating = ceil(avg_rating)

    if avg_rating > (floor_avg_rating+0.5) and avg_rating < ceil_avg_rating:
        avg_rating = float(floor_avg_rating+0.5)
    elif avg_rating > (floor_avg_rating) and avg_rating < (floor_avg_rating + 0.5):
        avg_rating = float(floor_avg_rating)

    context = {
        'single_product': single_product,
        'in_cart': in_cart,
        'reviews': reviews,
        'orderproduct_check': orderproduct_check,
        'avg_rating': avg_rating,
        'rating': len(reviews),
    }

    return render(request, 'store/product_detail.html', context)


# Search button functionality
def search(request):
    product_count = 0
    products = list()
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']

    if keyword:
        products = Product.objects.order_by(
            '-created_date').filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
        product_count = len(products)

    category_slug = "flag1"
    context = {
        'products': products,
        'product_count': product_count,
        'category_slug': category_slug,
    }
    return render(request, 'store/store.html', context)


# Review and rating
@login_required(login_url='login')
def submit_review(request, product_id):
    current_user = request.user

    # Current url
    url = request.META.get('HTTP_REFERER')
    if request.method == "POST":

        try:
            # to access the ForeignKey attributes we use "__" (double underscore) e.g product__id = product_id
            reviews = ReviewRating.objects.get(
                user=current_user, product__id=product_id)  # user__id= current_user.id
            # instance keyword is used,to check if data is already exist or not
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(
                request, 'Thank you! Your review has been updated.')
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = current_user.id
                data.save()

                messages.success(
                    request, "Thank you! Your review has been submitted.")
                return redirect(url)

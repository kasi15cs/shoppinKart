

from django.urls import path
from . import views

urlpatterns = [
    path('', views.cart, name='cart'),
    path('add_cart/<int:product_id>/', views.add_cart, name='add_cart'),
    path('remove_cart/<int:cart_item_id>/',
         views.remove_cart, name='remove_cart'),
    path('remove_cart_items/<int:cart_item_id>/',
         views.remove_cart_items, name='remove_cart_items'),

    path('checkout/', views.checkout, name='checkout'),

    path('billing_address/<int:billing_address_id>/',
         views.billing_address, name='billing_address'),

]

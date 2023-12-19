
from . import views
from django.urls import path


urlpatterns = [
    path('place_order/', views.place_order, name='place_order'),
    path('order_successful/', views.order_successful, name='order_successful'),
    path('create_payment/', views.create_payment, name='create_payment'),
    path('execute_payment/', views.execute_payment, name='execute_payment'),
    path('payment_failed/', views.payment_failed, name='payment_failed'),
    path('order_completed/', views.order_completed, name='order_completed'),

]

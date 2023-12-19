from . import views
from django.urls import path


urlpatterns = [
    path('manage_address/', views.manage_address, name='manage_address'),
    path('add_address/', views.add_address, name='add_address'),
    path('delete_address/<int:address_id>/',
         views.delete_address, name='delete_address'),
    path('edit_address/<int:address_id>/',
         views.edit_address, name='edit_address'),
    

]

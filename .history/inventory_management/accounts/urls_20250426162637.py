from django.urls import path
from .import views

urlpatterns = [
    path('login/',views.login_view,name ='login'),
    path('admin_home/',views.admin_home,name='admin_home'),
    path('buyer_home/',views.buyer_home,name ='buyer_home'),
    path('seller_home/',views.seller_home,name='seller_home'),
]
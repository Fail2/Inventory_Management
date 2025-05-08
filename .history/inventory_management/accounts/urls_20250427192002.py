from django.urls import path
from . import views

urlpatterns = [
    # Admin-related paths
    path('admin-login/', views.admin_login_view, name='admin_login'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # Buyer/Seller login
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Admin, Buyer, Seller Home
    path('admin_home/', views.admin_home, name='admin_home'),
    path('buyer_home/', views.buyer_home, name='buyer_home'),
    path('seller_home/', views.seller_home, name='seller_home'),

    # Buyer-specific paths
    path('buyers/', views.buyer_list, name='buyer_list'),
    path('buyers/add/', views.add_buyer, name='add_buyer'),
    path('buyer/login/', views.buyer_login, name='buyer_login'),
    path('buyer/home/', views.buyer_home, name='buyer_home'),

    #Supplier
    path('seller/home/', views.seller_home, name='seller_home'),
]

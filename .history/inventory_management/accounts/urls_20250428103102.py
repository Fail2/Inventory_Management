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
    #path('supplier/home/', views.supplier_home, name='supplier_home'),

    # Buyer-specific paths
    path('buyer/', views.buyer_list, name='buyer_list'),
    path('buyer/add/', views.add_buyer, name='add_buyer'),
    path('buyer/login/', views.login_view, name='login_view'),
    path('buyer/home/', views.buyer_home, name='buyer_home'),
    path('buyer/dashboard/', views.buyer_dashboard, name='buyer_dashboard'),
    path('buyer/place_order/<int:product_id>/', views.place_order, name='place_order'),

    #Supplier
    
]

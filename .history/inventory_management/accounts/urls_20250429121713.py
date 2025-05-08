from django.urls import path
from . import views

urlpatterns = [
    # Admin-related paths
    path('admin-login/', views.admin_login_view, name='admin_login'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('<str:user_type>/list/', views.user_list, name='user_list'),
    path('<str:user_type>/add/', views.add_user, name='add_user'),
    path('<str:user_type>/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('<str:user_type>/delete/<int:user_id>/', views.delete_user, name='delete_user'),

    # Buyer/Seller login
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Admin, Buyer, Seller Home
    path('admin_home/', views.admin_home, name='admin_home'),
    path('buyer_home/', views.buyer_home, name='buyer_home'),
    #path('supplier/home/', views.supplier_home, name='supplier_home'),

    # Buyer-specific paths
    path('buyer/login/', views.login_view, name='login_view'),
    path('buyer/home/', views.buyer_home, name='buyer_home'),
    path('buyer/orders/', views.order_history, name='order_history'),
    path('buyer/place_order/<int:product_id>/', views.place_order, name='place_order'),

    #Supplier
    
]

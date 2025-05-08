
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

urlpatterns = [
    # Admin-related paths
    path('admin-login/', views.admin_login_view, name='admin-login'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('<str:user_type>/list/', views.user_list, name='user_list'),
    path('<str:user_type>/add/', views.add_user, name='add_user'),
    path('<str:user_type>/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('<str:user_type>/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('products/', views.product_list, name='product_list'),
    path('add/', views.add_product, name='add_product'),  # add_product view coming next
    path('products/<int:product_id>/edit/', views.edit_product, name='edit_product'),
    path('products/<int:product_id>/delete/', views.delete_product, name='delete_product'),
    path('products/by/<str:group_by>/', views.grouped_product_list, name='grouped_product_list'),
    path('add/<str:group_by>/', views.add_group, name='add_group'),

    # Buyer/Seller login
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),


    # Buyer-specific paths
    path('buyer/login/', views.login_view, name='login_view'),
    path('buyer/home/', views.buyer_home, name='buyer_home'),
    path('buyer/orders/', views.order_history, name='order_history'),
    path('buyer/place_order/<int:product_id>/', views.place_order, name='place_order'),
    path('<str:user_type>/product/<int:product_id>/', views.buyer_product_detail, name='buyer_product_detail'),


    #Supplier
    
]


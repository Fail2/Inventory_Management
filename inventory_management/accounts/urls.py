
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
    path('manage/<str:group_by>/', views.manage_group, name='manage_group'),
    path('add/<str:group_by>/', views.add_group, name='add_group'),
    path('edit/<str:group_by>/<int:group_id>/', views.edit_group, name='edit_group'),
    path('delete/<str:group_by>/<int:group_id>/', views.delete_group, name='delete_group'),
    path('admin/orders/', views.admin_order_list, name='admin_order_list'),


    # Buyer/Seller login
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),


    # User-specific paths
    path('buyer/login/', views.buyer_login_request, name='buyer_login_request'),
    path('buyer/login/verify/', views.buyer_login_verify, name='buyer_login_verify'),
    path('buyer/register/complete/', views.buyer_complete_profile, name='buyer_complete_profile'),
    path('buyer/home/', views.buyer_home, name='buyer_home'),
    path('buyer/categories/', views.buyer_category_page, name='buyer_category'),
    path('buyer/cart/', views.cart_view, name='cart'),
    path('buyer/cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('buyer/cart/decrease/<int:product_id>/', views.decrease_cart_quantity, name='decrease_cart_quantity'),
    path('buyer/cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('buyer/wishlist/', views.wishlist_view, name='wishlist'),
    path('buyer/wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('buyer/orders/', views.buyer_orders, name='buyer_orders'),
    path('buyer/checkout/', views.checkout_view, name='checkout'),
    path('<str:user_type>/product/<int:product_id>/', views.buyer_product_detail, name='buyer_product_detail'),


    #Supplier
    path('supplier/login/', views.supplier_login_request, name='supplier_login_request'),
    path('supplier/login/verify/', views.supplier_login_verify, name='supplier_login_verify'),
    path('supplier/register/complete/', views.supplier_complete_profile, name='supplier_complete_profile'),
    path('supplier/home/', views.supplier_home, name='supplier_home'),

]


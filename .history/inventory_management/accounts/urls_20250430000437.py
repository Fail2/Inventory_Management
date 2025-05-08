
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
    path('add/', views.add_product, name='product_add'),  # add_product view coming next
    path('products/<int:pk>/edit/', views.edit_product, name='edit_product'),
    path('products/<int:pk>/delete/', views.delete_product, name='delete_product'),

    # Buyer/Seller login
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),


    # Buyer-specific paths
    path('buyer/login/', views.login_view, name='login_view'),
    path('buyer/home/', views.buyer_home, name='buyer_home'),
    path('buyer/orders/', views.order_history, name='order_history'),
    path('buyer/place_order/<int:product_id>/', views.place_order, name='place_order'),

    #Supplier
    
]

# This serves media files in development (make sure to only use this in development)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from django.urls import path
from .import views

urlpatterns = [
    path('login/',views.login_view,name ='login'),
    path('admin_home/',views.admin_home,name='admin_home'),
    path
]
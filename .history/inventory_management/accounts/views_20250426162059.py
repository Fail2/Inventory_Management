from django.shortcuts import redirect, render
from django.contrib.auth import authenticate,login
from django.contrib import messages
from django.http import HttpResponse
# Create your views here.


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password =request.POST['password']
        user_type =request.POST['user_type']

        user=authenticate(request,username = username,password = password)
        
        if user is not None and user.user_type == user_type:
            login(request,user)
            if user_type =='admin':
                return redirect('admin_home')
            elif user_type =='buyer':
                return redirect('buyer_home')
            elif user_type == 'seller':
                return redirect('seller_home')
        else:
            messages.error(request,'Invalid credentials or user type mismatch')

    return render(request,'accounts/login.html')           

def admin_home(request):
    return HttpResponse("Welcome Admin!")

def buyer_home(request):
    return HttpResponse("Welcome Buyer!")

def seller_home(request):
    return HttpResponse("Welcome Seller!")        
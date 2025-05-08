from django.shortcuts import redirect, render
from django.contrib.auth import authenticate,login
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
# Create your views here.


def admin_login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user is not None and user.user_type == 'admin':
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid admin credentials')

    return render(request, 'accounts/admin_login.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password =request.POST['password']
        user_type =request.POST['user_type']

        user=authenticate(request,username = username,password = password)
        
        if user is not None and user.user_type == user_type:
            login(request,user)
            if user_type =='buyer':
                return redirect('buyer_home')
            elif user_type == 'seller':
                return redirect('seller_home')
        else:
            messages.error(request,'Invalid credentials or user type mismatch')

    return render(request,'accounts/login.html')           

@login_required(login_url='login')
def admin_home(request):
    if request.user.user_type!='admin':
        return redirect('login')
    return HttpResponse("Welcome Admin!")

@login_required(login_url='login')
def buyer_home(request):
    if request.user.user_type !='buyer':
        return redirect('login')
    return HttpResponse("Welcome Buyer!")

@login_required(login_url='login')
def seller_home(request):
    if request.user.user_type !='seller':
        return redirect('login')
    return HttpResponse("Welcome Seller!")        
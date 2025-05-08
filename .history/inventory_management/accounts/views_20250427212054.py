from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from .models import Buyer,Supplier
from .forms import BuyerForm
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.hashers import make_password  #for converting the password to random looking long code

# Admin Login
def admin_login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        # Debugging: Check if username and password are correct
        print(f"Attempting login with username: {username}")

        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_superuser:  # Check if user is superuser
            print(f"Login successful for user: {user.username}")
            login(request, user)
            return redirect('admin_dashboard')  # Redirect to Admin Dashboard
        else:
            print("Login failed.")
            messages.error(request, 'Invalid admin credentials')

    return render(request, 'accounts/admin_login.html')


#admin-dashboard
@login_required(login_url='login')  # Redirect to login if not logged in
def admin_dashboard(request):
    if not request.user.is_superuser:  # Check if the user is an admin
        return redirect('login')  # If not admin, redirect to login page
    return render(request, 'accounts/admin_dashboard.html')

# Buyer/Seller Login
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user_type = request.POST['user_type']

        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.user_type == user_type:
            login(request, user)
            if user_type == 'buyer':
                return redirect('buyer_home')
            elif user_type == 'supplier':
                return redirect('supplier_home')
        else:
            messages.error(request, 'Invalid credentials or user type mismatch')

    return render(request, 'accounts/login.html')

# Admin Home
@login_required(login_url='login')
def admin_home(request):
    if not request.user.is_superuser:
        return redirect('login')
    return HttpResponse("Welcome Admin!")


# Buyer Home
@login_required(login_url='login')
def buyer_home(request):
    if request.user.user_type != 'buyer':
        return redirect('login')
    return HttpResponse("Welcome Buyer!")

# Seller Home
@login_required(login_url='login')
def supplier_home(request):
    if request.user.user_type != 'supplier':
        return redirect('login')
    return HttpResponse("Welcome Supplier!")

# Logout
@csrf_protect
def logout_view(request):
    if request.method == "POST":
        logout(request)
        return redirect('login')
    else:
        return redirect('admin_dashboard')  # or wherever you want if someone wrongly accesses via GET


#buyer_list
def buyer_list(request):
    buyers = Buyer.objects.all()
    return render(request, 'accounts/buyer_list.html', {
        'buyers': buyers,
        'title': 'Buyer List'
    })


#login for buyer/supplier
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user_type = request.POST.get('user_type')

        # Authenticate user based on user_type
        if user_type == 'buyer':
            try:
                buyer = Buyer.objects.get(username=username)
                if buyer.check_password(password):  # Check if the password matches
                    login(request, buyer)  # Log in the buyer
                    return redirect('buyer_home')  # Redirect to the buyer home page
                else:
                    messages.error(request, 'Invalid password for the buyer.')
            except Buyer.DoesNotExist:
                messages.error(request, 'Buyer with that username does not exist.')

        elif user_type == 'seller':
            try:
                seller = Seller.objects.get(username=username)
                if seller.check_password(password):  # Check if the password matches
                    login(request, seller)  # Log in the seller
                    return redirect('seller_home')  # Redirect to the seller home page
                else:
                    messages.error(request, 'Invalid password for the seller.')
            except Seller.DoesNotExist:
                messages.error(request, 'Seller with that username does not exist.')

    return render(request, 'accounts/login.html')
#add_buyer               
def add_buyer(request):
    if request.method == 'POST':
        form = BuyerForm(request.POST)
        if form.is_valid():
            # Save the buyer
            buyer = form.save(commit=False)
            buyer.password = make_password(form.cleaned_data['password'])  # Hash password
            buyer.save()

            # Send email to the buyer
            subject = 'Welcome to Inventory Management System'
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = [buyer.email]

            # Get the absolute URL for the login page
            login_url = request.build_absolute_uri('/accounts/login/')

            context = {
                'buyer': buyer,
                'plain_password': form.cleaned_data['password'],
                'login_url': login_url
            }

            html_content = render_to_string('accounts/buyer_email_template.html', context)
            email_message = EmailMultiAlternatives(subject, '', from_email, to_email)
            email_message.attach_alternative(html_content, "text/html")
            result = email_message.send()
            if result == 1:
               messages.success(request, 'Buyer added and email sent successfully!')
            else:
               messages.warning(request, 'Buyer added but email could not be sent.')

            return redirect('buyer_list')
    else:
        form = BuyerForm()

    return render(request, 'accounts/add_buyer.html', {'form': form})


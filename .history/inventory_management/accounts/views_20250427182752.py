from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from .models import Buyer 
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
            elif user_type == 'seller':
                return redirect('seller_home')
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
def seller_home(request):
    if request.user.user_type != 'seller':
        return redirect('login')
    return HttpResponse("Welcome Seller!")

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


#buyer_login
def buyer_login(request):
    if request.method =='POST':
        login_input = request.POST.get('login_input')  #username or email
        password = request.POST.get('password')

        try:
            buyer = Buyer.objects.filter(email=login_input).first()

            if buyer is None:
                buyer = Buyer.objects.filter(username = login_input).first()

            if buyer is not None and check_password(password,buyer.password):
                # Success - login buyer
                request.session['buyer_id'] = buyer.id
                request.session['buyer_name']= buyer.full_name 
                return redirect('buyer_dashboard')
            else:
                messages.error(request,'Invalid Login Credentials.')
        except Exception as e:
            messages.error(request, 'Something went wrong.')
    return render(request,'login.html')     

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

            context = {
                'buyer': buyer,
                'plain_password': form.cleaned_data['password'],
                'login_url': 'http://127.0.0.1:8000/accounts/login/'
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


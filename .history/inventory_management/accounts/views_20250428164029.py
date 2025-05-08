from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.contrib.messages.storage.fallback import FallbackStorage
from .models import Buyer,Supplier
from .models import Product, Order
from .forms import BuyerForm
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.hashers import make_password  #for converting the password to random looking long code
from django.contrib.auth.hashers import check_password

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
@login_required(login_url='admin-login')  # Redirect to admin-login if not logged in
def admin_dashboard(request):
    if not request.user.is_superuser:  # Check if the user is an admin
        return redirect('admin-login')  # If not admin, redirect to login page
    return render(request, 'accounts/admin_dashboard.html')

#buyer_list
def buyer_list(request):
    buyers = Buyer.objects.all()
    return render(request, 'accounts/buyer_list.html', {
        'buyers': buyers,
        'title': 'Buyer List'
    })

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
#edit_buyer

# Admin Home
@login_required(login_url='admin-login')
def admin_home(request):
    if not request.user.is_superuser:
        return redirect('admin-login')
    return HttpResponse("Welcome Admin!")



# Logout

# The logout view to handle POST logout request
@csrf_protect
def logout_view(request):
    if request.method == "POST":
        if request.user.is_superuser:
            # For superusers, log out normally (flush the session not required)
            logout(request)
            messages.success(request, "You have logged out successfully.")
            # Redirect superusers to admin-login page after logout
            return redirect('admin_login')  # Adjust the URL name as per your setup
        else:
            # Normal user logout (only clear specific session keys)
            if 'buyer_id' in request.session:
                del request.session['buyer_id']

            if 'supplier_id' in request.session:
                del request.session['supplier_id']

            # Manually restore the message storage after session flush
            if not hasattr(request, '_messages'):
                request._messages = FallbackStorage(request)

            messages.success(request, "You have logged out successfully.")  # Or personalized message
            logout(request)
            return redirect('login')
    else:
        # Check the user type and redirect accordingly if it's a GET request
        if request.user.is_authenticated:
            user_type = request.user.user_type  # Assuming you have a custom field 'user_type'

            if user_type == 'buyer':
                return redirect('buyer_home')  # Redirect to Buyer home page
            elif user_type == 'supplier':
                return redirect('supplier_home')  # Redirect to Supplier home page
            else:
                return redirect('admin_dashboard')  # Or any default home page
        else:
            # If the user is not authenticated, redirect to login
            return redirect('login')




#buyer_views
#buyer_dashboard
def buyer_dashboard(request):
    buyer_id = request.session.get('buyer_id')
    if not buyer_id:
        return redirect('login')

    orders = Order.objects.filter(buyer_id=buyer_id)
    return render(request, 'accounts/buyer_dashboard.html', {'orders': orders})
#buyer-home
def buyer_home(request):
    products = Product.objects.all()
    return render(request, 'accounts/buyer_home.html', {'products': products})
#order-history
def order_history(request):
    buyer_id = request.session.get('buyer_id')
    if not buyer_id:
        return redirect('login')
    orders = Order.objects.filter(buyer_id=buyer_id)
    return render(request, 'accounts/order_history.html', {'orders': orders})

#place-order
def place_order(request, product_id):
    if request.method == 'POST':
        buyer_id = request.session.get('buyer_id')
        if not buyer_id:
            return redirect('login')

        product = Product.objects.get(id=product_id)
        buyer = Buyer.objects.get(id=buyer_id)

        Order.objects.create(
            buyer=buyer,
            product=product,
            status='Pending'
        )
        messages.success(request, 'Order placed successfully!')
        return redirect('accounts/buyer_dashboard')


#login for buyer/supplier
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user_type = request.POST.get('user_type')  # buyer or supplier

        if user_type == 'buyer':
            try:
                buyer = Buyer.objects.get(username=username)
                if check_password(password, buyer.password):
                    # Set session manually (not Django's login(), because Buyer is custom model)
                    request.session['buyer_id'] = buyer.id
                    request.session['buyer_name'] = buyer.full_name
                    request.session['user_type'] = 'buyer'
                    
                    messages.success(request, 'Buyer login successful!')

                    next_url = request.GET.get('next', 'buyer_home')  
                    return redirect(next_url)
                else:
                    messages.error(request, 'Invalid password for the buyer.')
            except Buyer.DoesNotExist:
                messages.error(request, 'Buyer with that username does not exist.')

        elif user_type == 'supplier':
            try:
                supplier = Supplier.objects.get(username=username)
                if check_password(password, supplier.password):
                    request.session['supplier_id'] = supplier.id
                    request.session['supplier_name'] = supplier.full_name
                    request.session['user_type'] = 'supplier'

                    messages.success(request, 'Supplier login successful!')
                    return redirect('supplier_home')
                else:
                    messages.error(request, 'Invalid password for the supplier.')
            except Supplier.DoesNotExist:
                messages.error(request, 'Supplier with that username does not exist.')

    return render(request, 'accounts/login.html')





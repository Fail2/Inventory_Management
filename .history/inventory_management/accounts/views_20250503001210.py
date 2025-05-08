from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.contrib.messages.storage.fallback import FallbackStorage
from .models import Buyer,Supplier
from .models import Product, Order,Category,Season
from .forms import UserForm,ProductForm,DynamicGroupForm
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.hashers import make_password  #for converting the password to random looking long code
from django.contrib.auth.hashers import check_password
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

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


# Common List View (Buyer/Supplier)
@login_required(login_url='admin-login')
def user_list(request, user_type):
    if user_type == 'buyer':
        users = Buyer.objects.all()
        title = "Buyer List"
    elif user_type == 'supplier':
        users = Supplier.objects.all()
        title = "Supplier List"
    else:
        messages.error(request, "Invalid user type!")
        return redirect('admin_dashboard')  # fallback

    return render(request, 'accounts/user_list.html', {
        'users': users,
        'user_type': user_type,
        'title': title,
    })


# Common Add View (Buyer/Supplier)
@login_required(login_url='admin-login')
def add_user(request, user_type):
    if user_type == 'buyer':
        model_class = Buyer
        title = "Add Buyer"
    elif user_type == 'supplier':
        model_class = Supplier
        title = "Add Supplier"
    else:
        messages.error(request, "Invalid user type!")
        return redirect('admin_dashboard')

    if request.method == 'POST':
        form = UserForm(request.POST,model_class=model_class)
        if form.is_valid():
            user = form.save(commit=False)
            user.password = make_password(form.cleaned_data['password'])
            user.save()

            # Send Welcome Email
            subject = f'Welcome to Inventory Management System as {user_type.capitalize()}'
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = [user.email]

            login_url = request.build_absolute_uri('/accounts/login/')

            context = {
                'user': user,
                'plain_password': form.cleaned_data['password'],
                'login_url': login_url,
                'user_type': user_type
            }

            html_content = render_to_string('accounts/user_email_template.html', context)
            email_message = EmailMultiAlternatives(subject, '', from_email, to_email)
            email_message.attach_alternative(html_content, "text/html")
            result = email_message.send()

            if result == 1:
                messages.success(request, f'{user_type.capitalize()} added and email sent successfully!')
            else:
                messages.warning(request, f'{user_type.capitalize()} added but email could not be sent.')

            return redirect('user_list', user_type=user_type)
    else:
        form = UserForm(model_class=model_class)

    return render(request, 'accounts/add_user.html', {
        'form': form,
        'user_type': user_type,
        'title': title,
    })


# Common Edit View (Buyer/Supplier)
@login_required(login_url='admin-login')
def edit_user(request, user_type, user_id):
    if user_type == 'buyer':
        model_class = Buyer
        title = "Edit Buyer"
    elif user_type == 'supplier':
        model_class = Supplier
        title = "Edit Supplier"
    else:
        messages.error(request, "Invalid user type!")
        return redirect('admin_dashboard')

    user = get_object_or_404(model_class, id=user_id)

    if request.method == 'POST':
        form = UserForm(request.POST, instance=user,model_class=model_class)
        if form.is_valid():
            form.save()
            messages.success(request, f"{user_type.capitalize()} details updated successfully!")
            return redirect('user_list', user_type=user_type)
    else:
        form = UserForm(instance=user,model_class=model_class)

    return render(request, 'accounts/edit_user.html', {
        'form': form,
        'user_type': user_type,
        'title': title,
    })


# Common Delete View (Buyer/Supplier)
@login_required(login_url='admin-login')
def delete_user(request, user_type, user_id):
    if user_type == 'buyer':
        model_class = Buyer
    elif user_type == 'supplier':
        model_class = Supplier
    else:
        messages.error(request, "Invalid user type!")
        return redirect('admin-dashboard')

    user = get_object_or_404(model_class, id=user_id)

    if request.method == 'POST':
        user.delete()
        messages.success(request, f"{user_type.capitalize()} deleted successfully!")
        return redirect('user_list', user_type=user_type)

    return render(request, 'accounts/confirm_delete.html', {
        'user': user,
        'user_type': user_type,
    })

#product_list
@login_required(login_url='admin-login')
def product_list(request):
    products = Product.objects.all()
    return render(request, 'accounts/product_list.html', {'pro': products})

#add-product
# Ensure user is logged in
@login_required(login_url='admin-login')
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)  # include request.FILES here
        if form.is_valid():
            form.save()
            messages.success(request, "Product added successfully!")
            return redirect('product_list')
    else:
        form = ProductForm()

    return render(request, 'accounts/add_product.html', {'form': form, 'title': 'Add Product'})


#edit_product
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product_list')  # or wherever you want to redirect
    else:
        form = ProductForm(instance=product)

    return render(request, 'accounts/product_edit.html', {'form': form})
#delete-product
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == "POST":
        product.delete()
        return redirect('product_list')
    return render(request, 'accounts/product_delete.html', {'product': product})

#group by product
def grouped_product_list(request, group_by):
    # Step 1: Determine if we are working with category or season
    if group_by == 'category':
        groups = Category.objects.all()
        model_class = Category
    elif group_by == 'season':
        groups = Season.objects.all()
        model_class = Season
    else:
        messages.error(request, "Invalid group type!")
        return redirect('admin_dashboard')

    # Step 2: Get selected group (from dropdown)
    selected_group_id = request.GET.get('group_id')  # Comes from ?group_id= in URL
    selected_group = None

    if selected_group_id:
        try:
            selected_group = model_class.objects.get(id=selected_group_id)
        except model_class.DoesNotExist:
            messages.error(request, "Selected group does not exist.")
            selected_group = None
    elif groups.exists():
        selected_group = groups.first()  # If no group selected, use first one by default

    # Step 3: Fetch products for selected group
    if selected_group:
        products = Product.objects.filter(**{group_by: selected_group})
    else:
        products = Product.objects.none()  # Empty queryset if no group selected

    # Step 4: Set up pagination (6 products per page)
    paginator = Paginator(products, 6)
    page = request.GET.get('page', 1)
    try:
        paginated_products = paginator.page(page)
    except PageNotAnInteger:
        paginated_products = paginator.page(1)
    except EmptyPage:
        paginated_products = paginator.page(paginator.num_pages)

    # Step 5: Render the template with all needed data
    return render(request, 'accounts/grouped_product_list.html', {
        'group_by': group_by,
        'groups': groups,
        'selected_group': selected_group,
        'products': paginated_products,
    })

#add category/season

def add_group(request, group_by):
    if group_by not in ['category', 'season']:
        messages.error(request, 'Invalid group type.')
        return redirect('grouped_product_list', group_by=group_by)

    if request.method == 'POST':
        form = DynamicGroupForm(request.POST, group_by=group_by)
        if form.is_valid():
            form.save()
            messages.success(request, f'{group_by.capitalize()} added successfully!')
            return redirect('grouped_product_list', group_by=group_by)
    else:
        form = DynamicGroupForm(group_by=group_by)

    return render(request, 'accounts/add_group.html', {
        'form': form,
        'group_by': group_by,
    })


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
            return redirect('admin-login')  # Adjust the URL name as per your setup
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
                    return redirect('buyer_home')
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
                    return redirect('buyer_home')
                else:
                    messages.error(request, 'Invalid password for the supplier.')
            except Supplier.DoesNotExist:
                messages.error(request, 'Supplier with that username does not exist.')

    return render(request, 'accounts/login.html')



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
    # Get all categories
    categories = Category.objects.all()

    # Handle filtering by category
    selected_category_id = request.GET.get('category_id')
    
    if selected_category_id:
        # Filter products by selected category
        products = Product.objects.filter(category_id=selected_category_id)
    else:
        # Show all products if no category is selected
        products = Product.objects.all()

    context = {
        'categories': categories,
        'products': products,
        'selected_category_id': selected_category_id,
    }

    return render(request, 'accounts/buyer_home.html', context)

#product detail
@login_required(login_url='login')  # Ensure the user is logged in
def buyer_product_detail(request, user_type, product_id):
    # Get the product based on the ID
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        # Get the quantity and delivery address from the form
        quantity = int(request.POST.get('quantity'))
        address = request.POST.get('address')

        # Check if the quantity is valid
        if quantity < 1:
            return HttpResponse("Minimum order quantity is 1.", status=400)
        
        if quantity > product.quantity:
            return HttpResponse("Cannot order more than available stock.", status=400)

        # Create the order
        order = Order.objects.create(
            buyer=request.user.buyer,  # Assumes the logged-in user is a buyer
            product=product,
            quantity=quantity,
            delivery_address=address
        )

        # Update the product's quantity
        product.quantity -= quantity
        product.save()

        # Redirect to the orders page or confirmation page
        return redirect('buyer_orders')  # Adjust this to your orders page or confirmation view

    return render(request, 'accounts/buyer_product_detail.html', {'product': product})



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





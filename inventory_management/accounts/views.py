import logging
import random
from decimal import Decimal
from datetime import timedelta
from functools import wraps

from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.db import transaction
from django.utils import timezone
from .models import Buyer,Supplier
from .models import Product, OrderGroup, OrderItem, Category, Season, EmailOTP
from .forms import (
    ProductForm, DynamicGroupForm, EmailOTPRequestForm, OTPVerifyForm,
    BuyerProfileForm, SupplierProfileForm, BuyerAdminForm, SupplierAdminForm,
)
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.hashers import make_password  #for converting the password to random looking long code
from django.contrib.auth.hashers import check_password
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

logger = logging.getLogger(__name__)

OTP_EXPIRY_MINUTES = 10
OTP_RESEND_COOLDOWN_SECONDS = 60

# Admin Login
def admin_login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_superuser:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid admin credentials')

    return render(request, 'accounts/admin_login.html')


def admin_required(view_func):
    """Like @login_required, but also requires is_superuser. Every admin
    CRUD view is meant to be superuser-only; without this, an authenticated
    non-superuser CustomUser (is_staff=True, is_superuser=False) would have
    full access to every buyer/supplier/product/order management view."""
    @wraps(view_func)
    @login_required(login_url='admin-login')
    def wrapped(request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect('admin-login')
        return view_func(request, *args, **kwargs)
    return wrapped


#admin-dashboard
@admin_required
def admin_dashboard(request):
    pending_orders_qs = OrderGroup.objects.filter(status='pending').select_related('buyer', 'supplier')
    orders = pending_orders_qs.order_by('-order_date')[:6]
    pending_orders = pending_orders_qs.count()
    product_count = Product.objects.count()
    supplier_count = Supplier.objects.count()
    buyer_count = Buyer.objects.count()
    low_stock_products = Product.objects.filter(quantity__lte=5).order_by('quantity')[:5]

    return render(request, 'accounts/admin_dashboard.html', {
        'orders': orders,
        'order_count': pending_orders,
        'product_count': product_count,
        'supplier_count': supplier_count,
        'buyer_count': buyer_count,
        'low_stock_products': low_stock_products,
    })


# Common List View (Buyer/Supplier)
@admin_required
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
        'users': users.order_by('full_name'),
        'user_type': user_type,
        'title': title,
    })


ADMIN_FORM_CLASSES = {'buyer': BuyerAdminForm, 'supplier': SupplierAdminForm}


# Common Add View (Buyer/Supplier)
@admin_required
def add_user(request, user_type):
    if user_type == 'buyer':
        title = "Add Buyer"
    elif user_type == 'supplier':
        title = "Add Supplier"
    else:
        messages.error(request, "Invalid user type!")
        return redirect('admin_dashboard')

    form_class = ADMIN_FORM_CLASSES[user_type]

    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            user = form.save()

            # Send Welcome Email
            subject = f'Welcome to Inventory Management System as {user_type.capitalize()}'
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = [user.email]

            login_url = request.build_absolute_uri(reverse(f'{user_type}_login_request'))

            context = {
                'user': user,
                'login_url': login_url,
                'user_type': user_type,
            }

            html_content = render_to_string('accounts/user_email_template.html', context)
            email_message = EmailMultiAlternatives(subject, '', from_email, to_email)
            email_message.attach_alternative(html_content, "text/html")

            try:
                result = email_message.send()
            except Exception as exc:
                logger.exception("Failed to send welcome email to %s", user.email)
                messages.warning(request, f'{user_type.capitalize()} added successfully, but the welcome email could not be sent.')
            else:
                if result == 1:
                    messages.success(request, f'{user_type.capitalize()} added and email sent successfully!')
                else:
                    messages.warning(request, f'{user_type.capitalize()} added but email could not be sent.')

            return redirect('user_list', user_type=user_type)
    else:
        form = form_class()

    return render(request, 'accounts/add_user.html', {
        'form': form,
        'user_type': user_type,
        'title': title,
    })


# Common Edit View (Buyer/Supplier)
@admin_required
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

    form_class = ADMIN_FORM_CLASSES[user_type]
    user = get_object_or_404(model_class, id=user_id)

    if request.method == 'POST':
        form = form_class(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f"{user_type.capitalize()} details updated successfully!")
            return redirect('user_list', user_type=user_type)
    else:
        form = form_class(instance=user)

    return render(request, 'accounts/edit_user.html', {
        'form': form,
        'user_type': user_type,
        'user_obj': user,
        'title': title,
    })


# Common Delete View (Buyer/Supplier)
@admin_required
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

    return render(request, 'accounts/delete_user.html', {
        'user': user,
        'user_type': user_type,
    })

#product_list
@admin_required
def product_list(request):
    products = Product.objects.select_related('category', 'season').all()
    categories = Category.objects.all()
    seasons = Season.objects.all()

    return render(request, 'accounts/product_list.html', {
        'products': products,
        'categories': categories,
        'seasons': seasons,
    })

#add-product
# Ensure user is logged in
@admin_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)  # include request.FILES here
        if form.is_valid():
            form.save()
            messages.success(request, "Product added successfully!")
            return redirect('product_list')
    else:
        form = ProductForm()

    category_count = Category.objects.count()
    season_count = Season.objects.count()

    return render(request, 'accounts/add_product.html', {
        'form': form,
        'title': 'Add Product',
        'category_count': category_count,
        'season_count': season_count,
    })


#edit_product
@admin_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated successfully!")
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)

    category_count = Category.objects.count()
    season_count = Season.objects.count()

    return render(request, 'accounts/product_edit.html', {
        'form': form,
        'product': product,
        'category_count': category_count,
        'season_count': season_count,
    })
#delete-product
@admin_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == "POST":
        messages.success(request, f"{product.name} deleted successfully!")
        product.delete()
        return redirect('product_list')
    return render(request, 'accounts/product_delete.html', {'product': product})

#group by product
@admin_required
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
        except (model_class.DoesNotExist, ValueError):
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

#manage category/season
@admin_required
def manage_group(request, group_by):
    if group_by not in ['category', 'season']:
        messages.error(request, 'Invalid group type.')
        return redirect('admin_dashboard')

    if group_by == 'category':
        groups = Category.objects.all().order_by('name')
        model_class = Category
    else:
        groups = Season.objects.all().order_by('name')
        model_class = Season

    return render(request, 'accounts/manage_group.html', {
        'group_by': group_by,
        'groups': groups,
        'model_class': model_class,
    })


@admin_required
def add_group(request, group_by):
    if group_by not in ['category', 'season']:
        messages.error(request, 'Invalid group type.')
        return redirect('admin_dashboard')

    if request.method == 'POST':
        form = DynamicGroupForm(request.POST, group_by=group_by)
        if form.is_valid():
            form.save()
            messages.success(request, f'{group_by.capitalize()} added successfully!')
            return redirect('manage_group', group_by=group_by)
    else:
        form = DynamicGroupForm(group_by=group_by)

    return render(request, 'accounts/add_group.html', {
        'form': form,
        'group_by': group_by,
        'is_manage': True,
    })


@admin_required
def edit_group(request, group_by, group_id):
    if group_by not in ['category', 'season']:
        messages.error(request, 'Invalid group type.')
        return redirect('admin_dashboard')

    if group_by == 'category':
        model_class = Category
    else:
        model_class = Season

    group = get_object_or_404(model_class, id=group_id)

    if request.method == 'POST':
        form = DynamicGroupForm(request.POST, group_by=group_by)
        if form.is_valid():
            group.name = form.cleaned_data['name']
            group.save()
            messages.success(request, f'{group_by.capitalize()} updated successfully!')
            return redirect('manage_group', group_by=group_by)
    else:
        form = DynamicGroupForm(initial={'name': group.name}, group_by=group_by)

    return render(request, 'accounts/add_group.html', {
        'form': form,
        'group_by': group_by,
        'group': group,
        'is_manage': True,
    })


@admin_required
def delete_group(request, group_by, group_id):
    if group_by not in ['category', 'season']:
        messages.error(request, 'Invalid group type.')
        return redirect('admin_dashboard')

    if group_by == 'category':
        model_class = Category
    else:
        model_class = Season

    group = get_object_or_404(model_class, id=group_id)

    if request.method == 'POST':
        group.delete()
        messages.success(request, f'{group_by.capitalize()} deleted successfully!')
        return redirect('manage_group', group_by=group_by)

    return render(request, 'accounts/delete_group.html', {
        'group': group,
        'group_by': group_by,
    })

#admin_order_list

# Orders move forward one step at a time and can never be reverted or
# skipped. Admin can advance pending -> approved -> shipped; only the
# assigned supplier can advance shipped -> delivered (see supplier_home).
# Once delivered, an order is fully locked: no status change, no supplier
# reassignment, no deletion.
ORDER_STATUS_FLOW = ['pending', 'approved', 'shipped', 'delivered']


def _next_order_status(current_status):
    try:
        index = ORDER_STATUS_FLOW.index(current_status)
    except ValueError:
        return None
    if index + 1 < len(ORDER_STATUS_FLOW):
        return ORDER_STATUS_FLOW[index + 1]
    return None


@admin_required
def admin_order_list(request):
    orders = OrderGroup.objects.select_related('buyer', 'supplier').prefetch_related('items__product').order_by('-order_date')
    suppliers = Supplier.objects.all()
    status_choices = OrderGroup.STATUS_CHOICES
    selected_status = request.GET.get('status', '').strip()

    if selected_status:
        orders = orders.filter(status=selected_status)

    if request.method == 'POST':
        order_id = request.POST.get('order_id', '')
        order = OrderGroup.objects.filter(id=order_id).first() if order_id.isdigit() else None

        if order and order.status != 'delivered':
            if 'supplier_id' in request.POST:
                supplier_id = request.POST.get('supplier_id')
                if supplier_id:
                    if Supplier.objects.filter(id=supplier_id).exists():
                        order.supplier_id = supplier_id
                        order.save()
                else:
                    order.supplier_id = None
                    order.save()

            elif 'status' in request.POST:
                status = request.POST.get('status')
                # Admin may only advance one step forward, and never all the
                # way to 'delivered' - that transition belongs to the supplier.
                # Shipping also requires a supplier already be assigned,
                # otherwise the order becomes unreachable (no supplier
                # dashboard will ever show it to mark delivered).
                allowed_next = _next_order_status(order.status)
                if (status and status == allowed_next and status != 'delivered'
                        and not (status == 'shipped' and not order.supplier_id)):
                    order.status = status
                    order.save()

        return redirect('admin_order_list')

    return render(request, 'accounts/admin_order_list.html', {
        'orders': orders,
        'suppliers': suppliers,
        'status_choices': status_choices,
        'selected_status': selected_status,
    })


@admin_required
@require_POST
def delete_order(request, order_id):
    order = get_object_or_404(OrderGroup, id=order_id)
    if order.status != 'pending':
        messages.error(request, 'Only pending orders can be deleted.')
        return redirect('admin_order_list')

    with transaction.atomic():
        for item in order.items.all():
            product = Product.objects.select_for_update().get(id=item.product_id)
            product.quantity += item.quantity
            product.save()
        order.delete()

    messages.success(request, 'Order deleted and stock restored.')
    return redirect('admin_order_list')




# Logout

# The logout view to handle POST logout request
@csrf_protect
def logout_view(request):
    if request.method == "POST":
        # Buyer/supplier logins are session-only (no Django auth), so check
        # for those session keys first. This matters when an admin is also
        # signed in via Django auth in the same browser session — without
        # this priority, clicking "Logout" on the buyer/supplier navbar would
        # incorrectly bounce to the admin login page instead of clearing the
        # buyer/supplier session.
        if 'buyer_id' in request.session or 'supplier_id' in request.session:
            request.session.pop('buyer_id', None)
            request.session.pop('supplier_id', None)
            messages.success(request, "You have logged out successfully.")
            return redirect('buyer_home')

        if request.user.is_superuser:
            logout(request)
            messages.success(request, "You have logged out successfully.")
            # Redirect superusers to admin-login page after logout
            return redirect('admin-login')

        logout(request)
        messages.success(request, "You have logged out successfully.")
        return redirect('buyer_home')
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
            return redirect('buyer_home')


def csrf_failure(request, reason=""):
    """A stale tab (open across a token-rotating event like an admin login)
    will fail CSRF checks on its next form submit. Bounce back with a
    friendly message instead of Django's raw 403 page - the fresh page
    load that follows carries a valid token, so retrying just works."""
    messages.error(request, "Your session expired. Please try again.")
    referer = request.META.get('HTTP_REFERER')
    if referer and url_has_allowed_host_and_scheme(
        referer, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(referer)
    return redirect('buyer_home')


#neutral entry point: let the visitor pick buyer or supplier (both are email-OTP only now)
def login_view(request):
    return render(request, 'accounts/login.html')


#buyer and supplier both log in / self-register via a one-time email code
ROLE_CONFIG = {
    'buyer': {
        'model': Buyer,
        'session_id_key': 'buyer_id',
        'home_url': 'buyer_home',
        'profile_form': BuyerProfileForm,
        'role_label': 'Buyer',
        'alt_role': 'supplier',
    },
    'supplier': {
        'model': Supplier,
        'session_id_key': 'supplier_id',
        'home_url': 'supplier_home',
        'profile_form': SupplierProfileForm,
        'role_label': 'Supplier',
        'alt_role': 'buyer',
    },
}


def _is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def _cart_summary(cart):
    """Return (total, item_count) for a session cart dict, pricing against
    current Product records so it stays correct even if prices changed."""
    product_ids = [int(pid) for pid in cart.keys() if str(pid).isdigit()]
    products = {p.id: p for p in Product.objects.filter(id__in=product_ids)}
    total = Decimal('0.00')
    count = 0
    for pid, item in cart.items():
        product = products.get(int(pid)) if str(pid).isdigit() else None
        if not product:
            continue
        qty = int(item.get('quantity', 0))
        total += product.price * qty
        count += qty
    return total, count


def _ajax_step(request, template, context, action_url):
    # Django's messages framework only renders on a full page load (via the
    # messages partial), which the modal never does - without forwarding
    # them explicitly here, every messages.error()/warning() call before an
    # _ajax_step() (wrong code, expired code, cooldown, send failure, ...)
    # is silently swallowed and the user sees no feedback at all.
    pending_messages = [{'text': str(m), 'tags': m.tags} for m in messages.get_messages(request)]
    return JsonResponse({
        'html': render_to_string(template, context, request=request),
        'action_url': action_url,
        'messages': pending_messages,
    })


def _require_login(request, role):
    """Bounce an unauthenticated buyer/supplier action back to buyer_home
    with the sign-in modal auto-opened for that role, remembering where to
    return to afterwards. buyer_home is used as the landing page for both
    roles since that's where the shared login modal lives."""
    request.session['post_login_redirect'] = request.get_full_path()
    return redirect(f"{reverse('buyer_home')}?auth_required={role}")


def _post_login_target(request, config):
    next_url = request.session.pop('post_login_redirect', None)
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return next_url
    return reverse(config['home_url'])


def _otp_request_view(request, role):
    config = ROLE_CONFIG[role]
    ajax = _is_ajax(request)
    self_url = reverse(f'{role}_login_request')

    if request.method == 'POST':
        form = EmailOTPRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].lower().strip()

            recent_otp = EmailOTP.objects.filter(email=email, role=role, is_used=False).order_by('-created_at').first()
            if (recent_otp and not recent_otp.is_expired()
                    and (timezone.now() - recent_otp.created_at).total_seconds() < OTP_RESEND_COOLDOWN_SECONDS):
                request.session['otp_email'] = email
                request.session['otp_role'] = role
                messages.warning(request, 'A code was already sent. Please wait a moment before requesting another.')
                if ajax:
                    return _ajax_step(request, 'accounts/partials/otp_step_code.html',
                                       {'form': OTPVerifyForm(), 'email': email, 'role': role, **config},
                                       reverse(f'{role}_login_verify'))
                return redirect(f'{role}_login_verify')

            EmailOTP.objects.filter(email=email, role=role, is_used=False).update(is_used=True)

            code = f"{random.randint(0, 999999):06d}"
            EmailOTP.objects.create(
                email=email,
                role=role,
                code_hash=make_password(code),
                expires_at=timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES),
            )

            html_content = render_to_string('accounts/otp_email.html', {
                'code': code,
                'expiry_minutes': OTP_EXPIRY_MINUTES,
            })
            email_message = EmailMultiAlternatives(
                'Your verification code', '', settings.DEFAULT_FROM_EMAIL, [email]
            )
            email_message.attach_alternative(html_content, "text/html")

            try:
                email_message.send()
            except Exception:
                logger.exception("Failed to send OTP email to %s", email)
                messages.error(request, 'Could not send the verification email. Please try again shortly.')
                if ajax:
                    return _ajax_step(request, 'accounts/partials/otp_step_email.html',
                                       {'form': form, 'role': role, **config}, self_url)
                return render(request, 'accounts/otp_login_request.html', {'form': form, 'role': role, **config})

            request.session['otp_email'] = email
            request.session['otp_role'] = role
            messages.success(request, f'A verification code has been sent to {email}.')
            if ajax:
                return _ajax_step(request, 'accounts/partials/otp_step_code.html',
                                   {'form': OTPVerifyForm(), 'email': email, 'role': role, **config},
                                   reverse(f'{role}_login_verify'))
            return redirect(f'{role}_login_verify')

        if ajax:
            return _ajax_step(request, 'accounts/partials/otp_step_email.html',
                               {'form': form, 'role': role, **config}, self_url)
    else:
        form = EmailOTPRequestForm()

    if ajax:
        return _ajax_step(request, 'accounts/partials/otp_step_email.html',
                           {'form': form, 'role': role, **config}, self_url)
    return render(request, 'accounts/otp_login_request.html', {'form': form, 'role': role, **config})


def _otp_verify_view(request, role):
    config = ROLE_CONFIG[role]
    ajax = _is_ajax(request)
    email = request.session.get('otp_email')

    if not email or request.session.get('otp_role') != role:
        if ajax:
            return _ajax_step(request, 'accounts/partials/otp_step_email.html',
                               {'form': EmailOTPRequestForm(), 'role': role, **config},
                               reverse(f'{role}_login_request'))
        return redirect(f'{role}_login_request')

    if request.method == 'POST':
        form = OTPVerifyForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            otp = EmailOTP.objects.filter(email=email, role=role, is_used=False).order_by('-created_at').first()

            if not otp or otp.is_expired():
                messages.error(request, 'That code has expired. Please request a new one.')
                if ajax:
                    return _ajax_step(request, 'accounts/partials/otp_step_email.html',
                                       {'form': EmailOTPRequestForm(), 'role': role, **config},
                                       reverse(f'{role}_login_request'))
                return redirect(f'{role}_login_request')

            if otp.attempts >= EmailOTP.MAX_ATTEMPTS:
                messages.error(request, 'Too many incorrect attempts. Please request a new code.')
                if ajax:
                    return _ajax_step(request, 'accounts/partials/otp_step_email.html',
                                       {'form': EmailOTPRequestForm(), 'role': role, **config},
                                       reverse(f'{role}_login_request'))
                return redirect(f'{role}_login_request')

            if not check_password(code, otp.code_hash):
                otp.attempts += 1
                if otp.attempts >= EmailOTP.MAX_ATTEMPTS:
                    otp.is_used = True
                otp.save()
                messages.error(request, 'Incorrect code. Please try again.')
                if ajax:
                    return _ajax_step(request, 'accounts/partials/otp_step_code.html',
                                       {'form': form, 'email': email, 'role': role, **config},
                                       reverse(f'{role}_login_verify'))
                return render(request, 'accounts/otp_verify.html', {'form': form, 'email': email, 'role': role, **config})

            otp.is_used = True
            otp.save()
            del request.session['otp_email']
            del request.session['otp_role']

            account = config['model'].objects.filter(email=email).first()
            if account:
                request.session[config['session_id_key']] = account.id
                request.session['user_type'] = role
                messages.success(request, 'Login successful.')
                target = _post_login_target(request, config)
                if ajax:
                    return JsonResponse({'redirect': target})
                return redirect(target)

            request.session['pending_email'] = email
            request.session['pending_role'] = role
            if ajax:
                return _ajax_step(request, 'accounts/partials/otp_step_profile.html',
                                   {'form': config['profile_form'](), 'email': email, 'role': role, **config},
                                   reverse(f'{role}_complete_profile'))
            return redirect(f'{role}_complete_profile')

        if ajax:
            return _ajax_step(request, 'accounts/partials/otp_step_code.html',
                               {'form': form, 'email': email, 'role': role, **config},
                               reverse(f'{role}_login_verify'))
    else:
        form = OTPVerifyForm()

    if ajax:
        return _ajax_step(request, 'accounts/partials/otp_step_code.html',
                           {'form': form, 'email': email, 'role': role, **config},
                           reverse(f'{role}_login_verify'))
    return render(request, 'accounts/otp_verify.html', {'form': form, 'email': email, 'role': role, **config})


def _complete_profile_view(request, role):
    config = ROLE_CONFIG[role]
    ajax = _is_ajax(request)
    email = request.session.get('pending_email')

    if not email or request.session.get('pending_role') != role:
        if ajax:
            return _ajax_step(request, 'accounts/partials/otp_step_email.html',
                               {'form': EmailOTPRequestForm(), 'role': role, **config},
                               reverse(f'{role}_login_request'))
        return redirect(f'{role}_login_request')

    if request.method == 'POST':
        form = config['profile_form'](request.POST)
        if form.is_valid():
            account = form.save(commit=False)
            account.email = email
            account.save()

            del request.session['pending_email']
            del request.session['pending_role']
            request.session[config['session_id_key']] = account.id
            request.session['user_type'] = role

            messages.success(request, f'Welcome, {account.full_name}! Your account has been created.')
            target = _post_login_target(request, config)
            if ajax:
                return JsonResponse({'redirect': target})
            return redirect(target)

        if ajax:
            return _ajax_step(request, 'accounts/partials/otp_step_profile.html',
                               {'form': form, 'email': email, 'role': role, **config},
                               reverse(f'{role}_complete_profile'))
    else:
        form = config['profile_form']()

    if ajax:
        return _ajax_step(request, 'accounts/partials/otp_step_profile.html',
                           {'form': form, 'email': email, 'role': role, **config},
                           reverse(f'{role}_complete_profile'))
    return render(request, 'accounts/otp_complete_profile.html', {'form': form, 'email': email, 'role': role, **config})


def buyer_login_request(request):
    return _otp_request_view(request, 'buyer')

def buyer_login_verify(request):
    return _otp_verify_view(request, 'buyer')

def buyer_complete_profile(request):
    return _complete_profile_view(request, 'buyer')

def supplier_login_request(request):
    return _otp_request_view(request, 'supplier')

def supplier_login_verify(request):
    return _otp_verify_view(request, 'supplier')

def supplier_complete_profile(request):
    return _complete_profile_view(request, 'supplier')


def _account_info_view(request, role):
    config = ROLE_CONFIG[role]
    ajax = _is_ajax(request)
    account_id = request.session.get(config['session_id_key'])
    if not account_id:
        return _require_login(request, role)

    account = get_object_or_404(config['model'], id=account_id)

    if request.method == 'POST':
        form = config['profile_form'](request.POST, instance=account)
        if form.is_valid():
            form.save()
            if ajax:
                return JsonResponse({'success': True, 'message': 'Your info has been updated.'})
            messages.success(request, 'Your info has been updated.')
            return redirect(config['home_url'])
    else:
        form = config['profile_form'](instance=account)

    if ajax:
        html = render_to_string('accounts/partials/account_info_form.html',
                                 {'form': form, 'email': account.email}, request=request)
        return JsonResponse({'success': False, 'html': html})
    return render(request, 'accounts/account_info.html', {
        'form': form, 'email': account.email, 'role': role, 'role_label': config['role_label'],
    })


def buyer_account_info(request):
    return _account_info_view(request, 'buyer')

def supplier_account_info(request):
    return _account_info_view(request, 'supplier')


#buyer_views

#buyer-home
def buyer_home(request):
    products = Product.objects.select_related('category', 'season').all()

    query = request.GET.get('q', '').strip()
    selected_category_id = request.GET.get('category_id', '').strip()
    selected_season_id = request.GET.get('season_id', '').strip()
    price_max = request.GET.get('price_max', '').strip()

    if query:
        products = products.filter(name__icontains=query)
    if selected_category_id.isdigit():
        products = products.filter(category_id=selected_category_id)
    if selected_season_id.isdigit():
        products = products.filter(season_id=selected_season_id)
    if price_max:
        try:
            products = products.filter(price__lte=price_max)
        except Exception:
            pass

    featured_products = products.order_by('-id')[:8]
    new_arrivals = Product.objects.select_related('category', 'season').filter(
        created_at__gte=timezone.now() - timedelta(days=30)
    ).order_by('-created_at')[:8]

    context = {
        'products': featured_products,
        'new_arrivals': new_arrivals,
        'wishlist_ids': request.session.get('wishlist', []),
        'cart_product_ids': list(request.session.get('cart', {}).keys()),
        'selected_category_id': selected_category_id,
        'selected_season_id': selected_season_id,
        'query': query,
        'price_max': price_max,
    }

    return render(request, 'accounts/buyer_home.html', context)


def buyer_category_page(request):
    categories = Category.objects.all().order_by('name')
    seasons = Season.objects.all().order_by('name')

    products = Product.objects.select_related('category', 'season').all()

    query = request.GET.get('q', '').strip()
    selected_category_id = request.GET.get('category_id', '').strip()
    selected_season_id = request.GET.get('season_id', '').strip()
    price_max = request.GET.get('price_max', '').strip()

    if query:
        products = products.filter(name__icontains=query)
    if selected_category_id.isdigit():
        products = products.filter(category_id=selected_category_id)
    if selected_season_id.isdigit():
        products = products.filter(season_id=selected_season_id)
    if price_max:
        try:
            products = products.filter(price__lte=price_max)
        except Exception:
            pass

    products = products.order_by('-id')
    total_count = products.count()

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    wishlist_ids = request.session.get('wishlist', [])
    cart_product_ids = list(request.session.get('cart', {}).keys())

    if _is_ajax(request):
        html = render_to_string('accounts/partials/product_card_list.html', {
            'products': page_obj,
            'wishlist_ids': wishlist_ids,
            'cart_product_ids': cart_product_ids,
        }, request=request)
        return JsonResponse({'html': html, 'has_next': page_obj.has_next(), 'total_count': total_count})

    return render(request, 'accounts/buyer_category.html', {
        'products': page_obj,
        'total_count': total_count,
        'has_next': page_obj.has_next(),
        'categories': categories,
        'seasons': seasons,
        'selected_category_id': selected_category_id,
        'selected_season_id': selected_season_id,
        'query': query,
        'price_max': price_max,
        'wishlist_ids': wishlist_ids,
        'cart_product_ids': cart_product_ids,
    })


def cart_view(request):
    cart = request.session.get('cart', {})
    product_ids = [int(product_id) for product_id in cart.keys() if str(product_id).isdigit()]
    products = Product.objects.filter(id__in=product_ids)
    item_map = {str(product.id): product for product in products}

    cart_items = []
    total = 0
    for product_id, item in cart.items():
        product = item_map.get(product_id)
        if not product:
            continue
        quantity = int(item.get('quantity', 1))
        line_total = product.price * quantity
        total += line_total
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'line_total': line_total,
        })

    return render(request, 'accounts/cart.html', {
        'cart_items': cart_items,
        'total': total,
    })


@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})
    product_key = str(product.id)
    item = cart.get(product_key, {'quantity': 0})
    current_quantity = int(item.get('quantity', 0))
    ajax = _is_ajax(request)

    try:
        add_quantity = int(request.POST.get('quantity') or request.GET.get('quantity') or 1)
    except (TypeError, ValueError):
        add_quantity = 1
    add_quantity = max(1, add_quantity)

    if current_quantity + add_quantity > product.quantity:
        if product.quantity <= 0:
            message = f'{product.name} is out of stock.'
        elif current_quantity >= product.quantity:
            message = f'You already have the maximum available quantity of {product.name} in your cart.'
        else:
            message = f'Only {product.quantity - current_quantity} more unit(s) of {product.name} available.'
        if ajax:
            return JsonResponse({'success': False, 'message': message})
        if product.quantity <= 0:
            messages.error(request, message)
        else:
            messages.warning(request, message)
        return redirect('cart')

    new_quantity = current_quantity + add_quantity
    item['quantity'] = new_quantity
    cart[product_key] = item
    request.session['cart'] = cart

    if ajax:
        cart_total, cart_count = _cart_summary(cart)
        return JsonResponse({
            'success': True,
            'message': f'{product.name} added to cart.',
            'cart_count': cart_count,
            'quantity': new_quantity,
            'line_total': f'{product.price * new_quantity:.2f}',
            'cart_total': f'{cart_total:.2f}',
        })
    messages.success(request, f'{product.name} added to cart.')
    return redirect('cart')


@require_POST
def decrease_cart_quantity(request, product_id):
    cart = request.session.get('cart', {})
    product_key = str(product_id)
    item = cart.get(product_key)
    # Already gone (e.g. removed from another tab) - treat as removed so the
    # UI drops the row instead of showing a lingering "0 qty" line.
    removed = item is None
    new_quantity = 0

    if item:
        new_quantity = int(item.get('quantity', 1)) - 1
        if new_quantity <= 0:
            cart.pop(product_key, None)
            removed = True
        else:
            item['quantity'] = new_quantity
            cart[product_key] = item
        request.session['cart'] = cart

    if _is_ajax(request):
        cart_total, cart_count = _cart_summary(cart)
        line_total = None
        if not removed:
            product = Product.objects.filter(id=product_id).first()
            if product:
                line_total = f'{product.price * new_quantity:.2f}'
        return JsonResponse({
            'success': True,
            'removed': removed,
            'quantity': 0 if removed else new_quantity,
            'line_total': line_total,
            'cart_total': f'{cart_total:.2f}',
            'cart_count': cart_count,
        })

    return redirect('cart')


@require_POST
def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    cart.pop(str(product_id), None)
    request.session['cart'] = cart

    if _is_ajax(request):
        cart_total, cart_count = _cart_summary(cart)
        return JsonResponse({
            'success': True,
            'removed': True,
            'cart_total': f'{cart_total:.2f}',
            'cart_count': cart_count,
        })

    messages.success(request, 'Item removed from cart.')
    return redirect('cart')


def wishlist_view(request):
    wishlist_ids = request.session.get('wishlist', [])
    products = Product.objects.filter(id__in=wishlist_ids)
    return render(request, 'accounts/wishlist.html', {'products': products})


@require_POST
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist = request.session.get('wishlist', [])
    product_key = str(product.id)

    if product_key in wishlist:
        wishlist.remove(product_key)
        in_wishlist = False
        message = f'{product.name} removed from wishlist.'
    else:
        wishlist.append(product_key)
        in_wishlist = True
        message = f'{product.name} added to wishlist.'

    request.session['wishlist'] = wishlist

    if _is_ajax(request):
        return JsonResponse({
            'success': True,
            'in_wishlist': in_wishlist,
            'message': message,
            'wishlist_count': len(wishlist),
        })

    messages.success(request, message)
    referer = request.META.get('HTTP_REFERER')
    if referer and url_has_allowed_host_and_scheme(
        referer, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(referer)
    return redirect('buyer_home')

#product detail
def buyer_product_detail(request, user_type, product_id):
    product = get_object_or_404(Product, id=product_id)

    related_products = Product.objects.select_related('category', 'season').filter(category=product.category).exclude(id=product.id)[:4]
    seasonal_products = Product.objects.select_related('category', 'season').filter(season=product.season).exclude(id=product.id).exclude(id__in=[p.id for p in related_products])[:4]

    return render(request, 'accounts/buyer_product_detail.html', {
        'product': product,
        'related_products': related_products,
        'seasonal_products': seasonal_products,
        'wishlist_ids': request.session.get('wishlist', []),
        'cart_product_ids': list(request.session.get('cart', {}).keys()),
    })




#order-history
def buyer_orders(request):
    buyer_id = request.session.get('buyer_id')
    if not buyer_id:
        return _require_login(request, 'buyer')
    orders = OrderGroup.objects.filter(buyer_id=buyer_id).prefetch_related('items__product').order_by('-order_date')
    return render(request, 'accounts/buyer_orders.html', {'orders': orders})

#checkout - converts the cart into real orders
def checkout_view(request):
    buyer_id = request.session.get('buyer_id')
    if not buyer_id:
        return _require_login(request, 'buyer')
    buyer = get_object_or_404(Buyer, id=buyer_id)

    cart = request.session.get('cart', {})
    product_ids = [int(product_id) for product_id in cart.keys() if str(product_id).isdigit()]
    products = Product.objects.filter(id__in=product_ids)
    item_map = {str(product.id): product for product in products}

    cart_items = []
    total = Decimal('0.00')
    for product_id, item in cart.items():
        product = item_map.get(product_id)
        if not product:
            continue
        quantity = int(item.get('quantity', 1))
        line_total = product.price * quantity
        total += line_total
        cart_items.append({'product': product, 'quantity': quantity, 'line_total': line_total})

    if not cart_items:
        messages.error(request, 'Your cart is empty.')
        return redirect('cart')

    if request.method == 'POST':
        ajax = _is_ajax(request)
        delivery_address = request.POST.get('delivery_address', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()

        if not delivery_address or not phone_number:
            message = 'Delivery address and phone number are both required.'
            if ajax:
                return JsonResponse({'success': False, 'message': message})
            messages.error(request, message)
            return render(request, 'accounts/checkout.html', {
                'cart_items': cart_items,
                'total': total,
                'buyer': buyer,
                'phone_number': phone_number,
            })

        try:
            with transaction.atomic():
                order_group = OrderGroup.objects.create(
                    buyer=buyer,
                    delivery_address=delivery_address,
                    phone_number=phone_number,
                )
                for cart_item in cart_items:
                    # Re-check stock inside the transaction to avoid race conditions
                    product = Product.objects.select_for_update().get(id=cart_item['product'].id)
                    if cart_item['quantity'] > product.quantity:
                        raise ValueError(f'Not enough stock for {product.name}.')

                    OrderItem.objects.create(
                        order=order_group,
                        product=product,
                        quantity=cart_item['quantity'],
                        unit_price=product.price,
                    )
                    product.quantity -= cart_item['quantity']
                    product.save()
        except ValueError as exc:
            message = f'{exc} Please update your cart and try again.'
            if ajax:
                return JsonResponse({'success': False, 'message': message, 'redirect': reverse('cart')})
            messages.error(request, message)
            return redirect('cart')

        request.session['cart'] = {}
        messages.success(request, 'Order placed successfully!')
        if ajax:
            return JsonResponse({'success': True, 'redirect': reverse('buyer_orders')})
        return redirect('buyer_orders')

    return render(request, 'accounts/checkout.html', {
        'cart_items': cart_items,
        'total': total,
        'buyer': buyer,
    })

#supplier-home

def supplier_home(request):
    supplier_id = request.session.get('supplier_id')
    if not supplier_id:
        return _require_login(request, 'supplier')

    supplier = get_object_or_404(Supplier, id=supplier_id)

    # Fetch orders assigned to the supplier
    orders = OrderGroup.objects.select_related('buyer').prefetch_related('items').filter(supplier_id=supplier_id).order_by('-order_date')
    # Handle status update - a supplier may only mark a shipped order delivered
    if request.method == "POST":
        order_id = request.POST.get('order_id', '')
        status = request.POST.get('status')

        if status == 'delivered' and order_id.isdigit():
            order = OrderGroup.objects.filter(id=order_id, supplier_id=supplier_id, status='shipped').first()
            if order:
                order.status = 'delivered'
                order.save()

        return redirect('supplier_home')

    context = {
        'orders': orders,
        'supplier': supplier,
    }

    return render(request, 'accounts/supplier_home.html', context)





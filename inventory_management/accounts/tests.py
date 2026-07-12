from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Buyer, Category, Order, Product, Season, Supplier


class AddSupplierEmailFallbackTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='AdminPass123',
        )

    @patch('accounts.views.EmailMultiAlternatives.send', side_effect=Exception('SMTP auth failed'))
    def test_supplier_is_created_when_welcome_email_fails(self, mocked_send):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse('add_user', kwargs={'user_type': 'supplier'}),
            {
                'full_name': 'Test Supplier',
                'address': '123 Supplier Street',
                'email': 'supplier@example.com',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Supplier.objects.filter(email='supplier@example.com').exists())


class ProductListFilteringTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            username='admin2',
            email='admin2@example.com',
            password='AdminPass123',
        )
        self.category = Category.objects.create(name='Office')
        self.season = Season.objects.create(name='Winter')
        Product.objects.create(name='Ergonomic Chair', category=self.category, season=self.season, price='99.99', quantity=10)
        Product.objects.create(name='Standing Desk', category=self.category, season=self.season, price='149.00', quantity=5)

    def test_product_list_filters_by_name_query(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse('product_list'), {'q': 'ergonomic'})

        self.assertEqual(response.status_code, 200)
        self.assertIn('products', response.context)
        self.assertEqual(list(response.context['products']), [Product.objects.get(name='Ergonomic Chair')])


class AdminOrderListFilteringTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            username='admin3',
            email='admin3@example.com',
            password='AdminPass123',
        )
        self.category = Category.objects.create(name='Furniture')
        self.season = Season.objects.create(name='Spring')
        self.product = Product.objects.create(name='Office Lamp', category=self.category, season=self.season, price='45.00', quantity=20)
        self.buyer = Buyer.objects.create(full_name='Alice Buyer', address='1 Main St', email='alice@example.com')
        self.order = Order.objects.create(buyer=self.buyer, product=self.product, quantity=2, delivery_address='123 Main St', status='pending')

    def test_admin_order_list_filters_by_status(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse('admin_order_list'), {'status': 'pending'})

        self.assertEqual(response.status_code, 200)
        self.assertIn('orders', response.context)
        self.assertEqual(list(response.context['orders']), [self.order])


class AdminDashboardInventoryTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            username='admin4',
            email='admin4@example.com',
            password='AdminPass123',
        )
        self.category = Category.objects.create(name='Storage')
        self.season = Season.objects.create(name='Summer')
        Product.objects.create(name='Stapler', category=self.category, season=self.season, price='5.00', quantity=3)
        Product.objects.create(name='Notebook', category=self.category, season=self.season, price='2.50', quantity=12)

    def test_dashboard_includes_low_stock_products(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse('admin_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertIn('low_stock_products', response.context)
        self.assertEqual(list(response.context['low_stock_products']), [Product.objects.get(name='Stapler')])


class ProductFormDropdownVisibilityTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            username='admin5',
            email='admin5@example.com',
            password='AdminPass123',
        )

    def test_add_product_hides_category_and_season_fields_when_no_records_exist(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse('add_product'))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="category"')
        self.assertNotContains(response, 'name="season"')


class GroupManagementTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            username='admin6',
            email='admin6@example.com',
            password='AdminPass123',
        )
        Category.objects.create(name='Furniture')

    def test_manage_group_page_renders_for_category(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse('manage_group', kwargs={'group_by': 'category'}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Manage Category')
        self.assertContains(response, 'Furniture')


class BuyerStorefrontTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Shoes')
        self.season = Season.objects.create(name='Summer')
        self.product = Product.objects.create(name='Runner Shoes', category=self.category, season=self.season, price='120.00', quantity=10)

    def test_buyer_home_page_shows_storefront_sections(self):
        response = self.client.get(reverse('buyer_home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Featured Products')
        self.assertContains(response, 'Shop by Season')
        self.assertContains(response, 'Runner Shoes')

    def test_wishlist_page_shows_saved_products(self):
        session = self.client.session
        session['wishlist'] = [self.product.id]
        session.save()

        response = self.client.get(reverse('wishlist'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Wishlist')
        self.assertContains(response, self.product.name)

    def test_add_to_cart_stores_item_in_session(self):
        response = self.client.get(reverse('add_to_cart', args=[self.product.id]))

        self.assertEqual(response.status_code, 302)
        self.assertIn(str(self.product.id), self.client.session['cart'])
        self.assertEqual(self.client.session['cart'][str(self.product.id)]['quantity'], 1)

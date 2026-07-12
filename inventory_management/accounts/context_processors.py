# context_processors.py
from .models import Buyer, Supplier, Category, Season

def auth_status(request):
    current_buyer = None
    current_supplier = None

    buyer_id = request.session.get('buyer_id')
    supplier_id = request.session.get('supplier_id')

    if buyer_id:
        current_buyer = Buyer.objects.filter(id=buyer_id).first()
    if supplier_id:
        current_supplier = Supplier.objects.filter(id=supplier_id).first()

    return {
        'current_buyer': current_buyer,
        'current_supplier': current_supplier,
    }


def storefront_nav(request):
    cart = request.session.get('cart', {})
    wishlist = request.session.get('wishlist', [])
    cart_count = sum(int(item.get('quantity', 0)) for item in cart.values()) if isinstance(cart, dict) else 0

    return {
        'nav_categories': Category.objects.all().order_by('name'),
        'nav_seasons': Season.objects.all().order_by('name'),
        'nav_cart_count': cart_count,
        'nav_wishlist_count': len(wishlist),
    }

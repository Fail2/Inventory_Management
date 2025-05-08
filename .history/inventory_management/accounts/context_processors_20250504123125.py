# context_processors.py
from .models import Order, Buyer, Supplier, Product

def admin_stats(request):
    # Calculate counts dynamically
    order_count = Order.objects.filter(status='pending').count()
    buyer_count = Buyer.objects.count()
    supplier_count = Supplier.objects.count()
    product_count = Product.objects.count()

    return {
        'order_count': order_count,
        'buyer_count': buyer_count,
        'supplier_count': supplier_count,
        'product_count': product_count,
    }

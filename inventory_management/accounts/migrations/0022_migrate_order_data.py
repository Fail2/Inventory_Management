from decimal import Decimal

from django.db import migrations


def migrate_orders_forward(apps, schema_editor):
    Order = apps.get_model('accounts', 'Order')
    OrderGroup = apps.get_model('accounts', 'OrderGroup')
    OrderItem = apps.get_model('accounts', 'OrderItem')

    for order in Order.objects.all():
        group = OrderGroup.objects.create(
            buyer_id=order.buyer_id,
            supplier_id=order.supplier_id,
            delivery_address=order.delivery_address,
            phone_number=order.phone_number,
            status=order.status,
        )
        # order_date has auto_now_add=True, which just stamped "now" on
        # create above - restore the original timestamp via update() since
        # that bypasses the auto_now_add behavior on save().
        OrderGroup.objects.filter(pk=group.pk).update(order_date=order.order_date)

        quantity = order.quantity or 1
        if order.total_amount is not None:
            unit_price = order.total_amount / quantity
        elif order.product_id:
            unit_price = order.product.price
        else:
            unit_price = Decimal('0.00')

        OrderItem.objects.create(
            order_id=group.pk,
            product_id=order.product_id,
            quantity=quantity,
            unit_price=unit_price,
        )


def migrate_orders_backward(apps, schema_editor):
    OrderGroup = apps.get_model('accounts', 'OrderGroup')
    OrderGroup.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0021_add_order_group_and_item'),
    ]

    operations = [
        migrations.RunPython(migrate_orders_forward, migrate_orders_backward),
    ]

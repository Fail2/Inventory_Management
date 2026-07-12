from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0022_migrate_order_data'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Order',
        ),
    ]

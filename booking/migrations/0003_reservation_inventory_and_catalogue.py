from decimal import Decimal
from django.db import migrations, models


def seed_city_catalogue(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    Profile = apps.get_model('booking', 'Profile')
    Hotel = apps.get_model('booking', 'Hotel')
    Room = apps.get_model('booking', 'Room')
    manager, _ = User.objects.get_or_create(username='hotel_manager', defaults={'first_name': 'Demo Manager', 'email': 'manager@stayora.demo'})
    Profile.objects.get_or_create(user=manager, defaults={'role': 'MANAGER', 'location': 'Bengaluru'})
    hotels = [
        ('The Garden Residency', '12 MG Road', 'Bengaluru', 'Karnataka, India'), ('Indiranagar Urban Stay', '45 100 Feet Road', 'Bengaluru', 'Karnataka, India'),
        ('Cubbon Park Grand', '18 Kasturba Road', 'Bengaluru', 'Karnataka, India'), ('Koramangala House', '7 80 Feet Road', 'Bengaluru', 'Karnataka, India'),
        ('Whitefield Suites', '9 ITPL Main Road', 'Bengaluru', 'Karnataka, India'), ('Lakeside HSR Hotel', '31 HSR Layout', 'Bengaluru', 'Karnataka, India'),
        ('Nandi Hills Retreat', '65 Palace Road', 'Bengaluru', 'Karnataka, India'), ('Brigade Road Boutique', '22 Brigade Road', 'Bengaluru', 'Karnataka, India'),
        ('Jayanagar Comfort Inn', '14 4th Block', 'Bengaluru', 'Karnataka, India'), ('Bellandur Bay Stay', '3 Outer Ring Road', 'Bengaluru', 'Karnataka, India'),
        ('Mysore Heritage Inn', '8 Palace Road', 'Mysuru', 'Karnataka, India'), ('Delhi City Haven', '19 Connaught Place', 'New Delhi', 'Delhi, India'),
    ]
    images = ['https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=900&q=80', 'https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=900&q=80', 'https://images.unsplash.com/photo-1564501049412-61c2a3083791?auto=format&fit=crop&w=900&q=80']
    for i, (name, address, city, region) in enumerate(hotels):
        hotel, _ = Hotel.objects.get_or_create(name=name, city=city, defaults={'manager': manager, 'address': address, 'state_country': region, 'description': 'A polished, welcoming stay with thoughtful service, comfortable rooms, and easy access to the city.', 'contact_number': '08012345678', 'email': f'hotel{i}@stayora.demo', 'amenities': 'Wi-Fi, Breakfast, Parking, Swimming pool, Gym, Air conditioning', 'image_url': images[i % len(images)], 'status': 'ACTIVE'})
        Room.objects.get_or_create(hotel=hotel, number='DELUXE', defaults={'room_type': 'DELUXE', 'price_per_night': Decimal(3200 + i * 180), 'max_guests': 2, 'inventory': 6, 'description': 'Bright deluxe room with premium bedding.', 'amenities': 'Wi-Fi, Breakfast, Air conditioning'})
        Room.objects.get_or_create(hotel=hotel, number='SUITE', defaults={'room_type': 'SUITE', 'price_per_night': Decimal(5400 + i * 220), 'max_guests': 4, 'inventory': 3, 'description': 'Spacious suite with lounge area.', 'amenities': 'Wi-Fi, Breakfast, Pool access, Gym'})


class Migration(migrations.Migration):
    dependencies = [('booking', '0002_demo_catalogue')]
    operations = [
        migrations.AddField(model_name='room', name='inventory', field=models.PositiveSmallIntegerField(default=5, help_text='Rooms of this category available to sell')),
        migrations.AddField(model_name='booking', name='rooms_count', field=models.PositiveSmallIntegerField(default=1)),
        migrations.CreateModel(name='Refund', fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('amount', models.DecimalField(decimal_places=2, max_digits=12)), ('reference', models.CharField(max_length=40, unique=True)), ('status', models.CharField(default='PROCESSED', max_length=20)), ('created_at', models.DateTimeField(auto_now_add=True)), ('payment', models.OneToOneField(on_delete=models.deletion.PROTECT, related_name='refund', to='booking.payment'))]),
        migrations.RunPython(seed_city_catalogue, migrations.RunPython.noop),
    ]

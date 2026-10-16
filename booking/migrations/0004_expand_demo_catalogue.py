from decimal import Decimal

from django.db import migrations


def expand_demo_catalogue(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    Profile = apps.get_model('booking', 'Profile')
    Hotel = apps.get_model('booking', 'Hotel')
    Room = apps.get_model('booking', 'Room')

    manager, _ = User.objects.get_or_create(
        username='hotel_manager',
        defaults={'first_name': 'Demo Manager', 'email': 'manager@stayora.demo'},
    )
    Profile.objects.get_or_create(
        user=manager,
        defaults={'role': 'MANAGER', 'location': 'Bengaluru'},
    )

    cities = [
        ('Bengaluru', 'Karnataka, India'),
        ('Kolkata', 'West Bengal, India'),
        ('Chennai', 'Tamil Nadu, India'),
        ('Mumbai', 'Maharashtra, India'),
        ('New Delhi', 'Delhi, India'),
        ('Dehradun', 'Uttarakhand, India'),
        ('Srinagar', 'Jammu and Kashmir, India'),
        ('Pune', 'Maharashtra, India'),
        ('Hyderabad', 'Telangana, India'),
        ('Jaipur', 'Rajasthan, India'),
        ('Panaji', 'Goa, India'),
        ('Kochi', 'Kerala, India'),
        ('Ahmedabad', 'Gujarat, India'),
        ('Lucknow', 'Uttar Pradesh, India'),
        ('Udaipur', 'Rajasthan, India'),
    ]
    hotel_styles = [
        'Grand Residency', 'Cityscape Hotel', 'Garden Retreat', 'Urban Nest',
        'Heritage House', 'Lakeside Suites', 'Central Inn', 'Crown Comfort',
        'Palm Grove Hotel', 'Skyline Stay',
    ]
    images = [
        'https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=80',
        'https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=1200&q=80',
        'https://images.unsplash.com/photo-1564501049412-61c2a3083791?auto=format&fit=crop&w=1200&q=80',
        'https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?auto=format&fit=crop&w=1200&q=80',
        'https://images.unsplash.com/photo-1584132967334-10e028bd69f7?auto=format&fit=crop&w=1200&q=80',
    ]
    room_types = [
        ('SINGLE', 'Single', Decimal('1400'), 1),
        ('DOUBLE', 'Double', Decimal('1900'), 2),
        ('DELUXE', 'Deluxe', Decimal('2500'), 2),
        ('FAMILY', 'Family', Decimal('3200'), 4),
        ('SUITE', 'Suite', Decimal('3900'), 4),
    ]

    for city_index, (city, region) in enumerate(cities):
        for hotel_index, style in enumerate(hotel_styles):
            name = f'{city} {style}'
            hotel, _ = Hotel.objects.get_or_create(
                name=name,
                city=city,
                defaults={
                    'manager': manager,
                    'address': f'{hotel_index + 1} {city} Central Road',
                    'state_country': region,
                    'description': f'A comfortable, well-located stay for exploring {city}.',
                    'contact_number': '08012345678',
                    'email': f'{city_index}-{hotel_index}@stayora.demo',
                    'amenities': 'Wi-Fi, Breakfast, Parking, Air conditioning, Restaurant',
                    'image_url': images[(city_index + hotel_index) % len(images)],
                    'status': 'ACTIVE',
                },
            )
            for room_index, (code, label, base_price, guests) in enumerate(room_types):
                Room.objects.update_or_create(
                    hotel=hotel,
                    number=code,
                    defaults={
                        'room_type': code,
                        'price_per_night': base_price + (hotel_index * 75) + (city_index * 25),
                        'max_guests': guests,
                        'description': f'Comfortable {label.lower()} room at {name}.',
                        'amenities': 'Wi-Fi, Air conditioning, Fresh linen',
                        'inventory': 4,
                        'is_active': True,
                    },
                )


class Migration(migrations.Migration):
    dependencies = [('booking', '0003_reservation_inventory_and_catalogue')]

    operations = [migrations.RunPython(expand_demo_catalogue, migrations.RunPython.noop)]

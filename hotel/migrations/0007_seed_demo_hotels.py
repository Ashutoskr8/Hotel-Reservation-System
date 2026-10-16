from decimal import Decimal
from django.db import migrations


def seed_hotels(apps, schema_editor):
    User = apps.get_model('hotel', 'User')
    Hotel = apps.get_model('hotel', 'Hotel')
    Room = apps.get_model('hotel', 'Room')
    manager, _ = User.objects.get_or_create(
        username='demo_manager',
        defaults={'name': 'Demo Hotel Manager', 'password': 'not-for-login', 'role': 'MANAGER'},
    )
    entries = [
        ('The Garden Residency', '12 MG Road', 'Bengaluru', 'Karnataka, India', 'A calm city-centre stay near shopping and metro connections.', 'Wi-Fi, Breakfast, Parking, Air conditioning', [('101', 'DELUXE', '4500.00', 2), ('201', 'SUITE', '7800.00', 3)]),
        ('Indiranagar Urban Stay', '45 100 Feet Road', 'Bengaluru', 'Karnataka, India', 'Contemporary rooms close to cafés and business districts.', 'Wi-Fi, Gym, Restaurant, Airport transfer', [('301', 'DOUBLE', '3900.00', 2), ('302', 'FAMILY', '6200.00', 4)]),
        ('Mysore Heritage Inn', '8 Palace Road', 'Mysuru', 'Karnataka, India', 'Comfortable rooms close to Mysore Palace.', 'Wi-Fi, Parking, Breakfast', [('11', 'SINGLE', '2400.00', 1)]),
    ]
    for name, address, city, region, description, amenities, rooms in entries:
        hotel, _ = Hotel.objects.get_or_create(
            name=name, city=city,
            defaults={'manager': manager, 'address': address, 'state_country': region, 'description': description, 'contact_number': '08012345678', 'email': f'{city.lower()}@stayfinder.demo', 'amenities': amenities, 'status': 'ACTIVE'},
        )
        for number, room_type, price, guests in rooms:
            Room.objects.get_or_create(hotel=hotel, room_number=number, defaults={'room_type': room_type, 'price_per_night': Decimal(price), 'max_guests': guests, 'description': f'{room_type.title()} room at {name}', 'amenities': amenities})


def remove_seed_hotels(apps, schema_editor):
    Hotel = apps.get_model('hotel', 'Hotel')
    Hotel.objects.filter(name__in=['The Garden Residency', 'Indiranagar Urban Stay', 'Mysore Heritage Inn']).delete()


class Migration(migrations.Migration):
    dependencies = [('hotel', '0006_hotel_book_history_fare_hotel_book_history_from_date_and_more')]
    operations = [migrations.RunPython(seed_hotels, remove_seed_hotels)]

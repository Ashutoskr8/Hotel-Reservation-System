from decimal import Decimal
from django.db import migrations


def create_catalogue(apps, schema_editor):
    User = apps.get_model('auth', 'User'); Profile = apps.get_model('booking', 'Profile'); Hotel = apps.get_model('booking', 'Hotel'); Room = apps.get_model('booking', 'Room')
    manager, _ = User.objects.get_or_create(username='hotel_manager', defaults={'first_name':'Demo Manager', 'email':'manager@hotelhub.demo'})
    Profile.objects.get_or_create(user=manager, defaults={'role':'MANAGER', 'location':'Bengaluru'})
    catalogue = [
        ('The Garden Residency', '12 MG Road', 'Bengaluru', 'Karnataka, India', 'A refined city-centre stay beside shopping and metro connections.', 'Wi-Fi, Breakfast, Parking, Air conditioning', [('101','DELUXE','4500',2),('201','SUITE','7800',3)]),
        ('Indiranagar Urban Stay', '45 100 Feet Road', 'Bengaluru', 'Karnataka, India', 'Modern rooms near Bengaluru cafes and business districts.', 'Wi-Fi, Gym, Restaurant, Airport transfer', [('301','DOUBLE','3900',2),('302','FAMILY','6200',4)]),
        ('Mysore Heritage Inn', '8 Palace Road', 'Mysuru', 'Karnataka, India', 'Comfortable rooms close to Mysore Palace.', 'Wi-Fi, Parking, Breakfast', [('11','SINGLE','2400',1)]),
    ]
    for name, address, city, region, description, amenities, rooms in catalogue:
        hotel, _ = Hotel.objects.get_or_create(name=name, city=city, defaults={'manager':manager,'address':address,'state_country':region,'description':description,'contact_number':'08012345678','email':f'{city.lower()}@hotelhub.demo','amenities':amenities,'status':'ACTIVE'})
        for number, kind, price, guests in rooms: Room.objects.get_or_create(hotel=hotel, number=number, defaults={'room_type':kind,'price_per_night':Decimal(price),'max_guests':guests,'description':f'{kind.title()} room at {name}','amenities':amenities})


class Migration(migrations.Migration):
    dependencies = [('booking', '0001_initial')]
    operations = [migrations.RunPython(create_catalogue, migrations.RunPython.noop)]

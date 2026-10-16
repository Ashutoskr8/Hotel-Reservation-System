from django.contrib import admin
from .models import Booking, Hotel, Payment, Profile, Review, Room
admin.site.register([Profile, Hotel, Room, Booking, Payment, Review])

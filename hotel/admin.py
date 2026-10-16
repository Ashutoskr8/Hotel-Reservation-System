from django.contrib import admin
from hotel.models import *
# Register your models here.
admin.site.register(User)
admin.site.register(Profile)
admin.site.register(Hotel_book)
admin.site.register(Hotel_book_history)
admin.site.register(Hotel)
admin.site.register(Room)
admin.site.register(Reservation)
admin.site.register(Payment)
admin.site.register(Review)

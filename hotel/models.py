from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone

# Create your models here.
class User(models.Model):
    username=models.CharField(primary_key=True,max_length=20)
    password=models.CharField(max_length=128)
    name=models.CharField(max_length=30)
    ROLE_CHOICES = [('CUSTOMER', 'Customer'), ('MANAGER', 'Hotel manager'), ('ADMIN', 'Admin')]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='CUSTOMER')
    def __str__(self):
        return self.username
    
class Profile(models.Model):
    username=models.ForeignKey(User,primary_key=True,max_length=20,on_delete=models.CASCADE)
    fathers_name=models.CharField(max_length=30,default='not filled')
    mothers_name=models.CharField(max_length=30,default='not filled')
    email=models.CharField(max_length=30,default='not filled')
    phone=models.CharField(max_length=10,default='not filled')
    location=models.CharField(max_length=100,default='', blank=True)
    def __str__(self):
        return self.fathers_name

class Hotel_book(models.Model):
    username=models.ForeignKey(User,primary_key=True,max_length=20,on_delete=models.CASCADE)
    from_date=models.CharField(max_length=30)
    to_date=models.CharField(max_length=30)
    hotel_name=models.CharField(max_length=30)
    def __str__(self):
        return self.from_date

class hotel_fare:
    hotel_name=models.CharField(max_length=30)
    room_type=models.CharField(max_length=30)
    fare=models.IntegerField(default=0)

class Hotel_book_history(models.Model):
    book_id=models.CharField(max_length=30,primary_key=True)
    username=models.ForeignKey(User,on_delete=models.CASCADE)
    from_date=models.CharField(max_length=30, default='')
    to_date=models.CharField(max_length=30, default='')
    hotel_name=models.CharField(max_length=30, default='')
    room_type=models.CharField(max_length=30, default='')
    fare=models.IntegerField(default=0)


# The original models above are retained so existing accounts/data continue to work.
# These models power the date-aware reservation workflow.
class Hotel(models.Model):
    STATUS_CHOICES = [('PENDING', 'Pending approval'), ('ACTIVE', 'Active'), ('INACTIVE', 'Inactive')]
    manager = models.ForeignKey(User, on_delete=models.PROTECT, related_name='managed_hotels')
    name = models.CharField(max_length=120)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=80, db_index=True)
    state_country = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    contact_number = models.CharField(max_length=20)
    email = models.EmailField()
    check_in_time = models.TimeField(default='14:00')
    check_out_time = models.TimeField(default='11:00')
    amenities = models.CharField(max_length=500, blank=True, help_text='Comma-separated amenities')
    image_url = models.URLField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self): return self.name

    @property
    def rating(self):
        return self.reviews.filter(is_visible=True).aggregate(models.Avg('rating'))['rating__avg'] or 0


class Room(models.Model):
    ROOM_TYPES = [('SINGLE', 'Single'), ('DOUBLE', 'Double'), ('DELUXE', 'Deluxe'), ('SUITE', 'Suite'), ('FAMILY', 'Family')]
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='rooms')
    room_number = models.CharField(max_length=20)
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    max_guests = models.PositiveSmallIntegerField(default=2)
    description = models.TextField(blank=True)
    amenities = models.CharField(max_length=500, blank=True)
    image_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('hotel', 'room_number')
        ordering = ['hotel', 'room_number']

    def __str__(self): return f'{self.hotel.name} — {self.room_number}'


class Reservation(models.Model):
    STATUS_CHOICES = [('PENDING', 'Pending'), ('CONFIRMED', 'Confirmed'), ('CANCELLED', 'Cancelled'), ('COMPLETED', 'Completed')]
    customer = models.ForeignKey(User, on_delete=models.PROTECT, related_name='reservations')
    hotel = models.ForeignKey(Hotel, on_delete=models.PROTECT, related_name='reservations')
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name='reservations')
    check_in = models.DateField()
    check_out = models.DateField()
    guests = models.PositiveSmallIntegerField(default=1)
    rooms_count = models.PositiveSmallIntegerField(default=1)
    nights = models.PositiveSmallIntegerField()
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(default=timezone.now)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self): return f'Booking #{self.pk}'


class Payment(models.Model):
    STATUS_CHOICES = [('PENDING', 'Pending'), ('SUCCESS', 'Success'), ('FAILED', 'Failed'), ('REFUNDED', 'Refunded')]
    METHODS = [('CARD', 'Card'), ('UPI', 'UPI'), ('NETBANKING', 'Net banking'), ('CASH', 'Cash at hotel')]
    reservation = models.OneToOneField(Reservation, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=12, choices=METHODS)
    transaction_id = models.CharField(max_length=40, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    paid_at = models.DateTimeField(null=True, blank=True)
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    refunded_at = models.DateTimeField(null=True, blank=True)


class Review(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='reviews')
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    is_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('hotel', 'customer')

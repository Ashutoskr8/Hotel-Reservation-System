from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Profile(models.Model):
    CUSTOMER, MANAGER = 'CUSTOMER', 'MANAGER'
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='booking_profile')
    role = models.CharField(max_length=12, choices=[(CUSTOMER, 'Customer'), (MANAGER, 'Hotel manager')], default=CUSTOMER)
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=100, blank=True)


class Hotel(models.Model):
    PENDING, ACTIVE, INACTIVE = 'PENDING', 'ACTIVE', 'INACTIVE'
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='managed_hotels')
    name = models.CharField(max_length=140)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=80, db_index=True)
    state_country = models.CharField(max_length=100)
    description = models.TextField()
    contact_number = models.CharField(max_length=20)
    email = models.EmailField()
    check_in_time = models.TimeField(default='14:00')
    check_out_time = models.TimeField(default='11:00')
    amenities = models.CharField(max_length=500, blank=True)
    image_url = models.URLField(blank=True)
    status = models.CharField(max_length=10, choices=[(PENDING, 'Pending'), (ACTIVE, 'Active'), (INACTIVE, 'Inactive')], default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['name']
    def __str__(self): return self.name
    @property
    def rating(self): return self.reviews.filter(is_visible=True).aggregate(models.Avg('rating'))['rating__avg'] or 0


class Room(models.Model):
    TYPES = [('SINGLE','Single'),('DOUBLE','Double'),('DELUXE','Deluxe'),('SUITE','Suite'),('FAMILY','Family')]
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='rooms')
    number = models.CharField(max_length=20)
    room_type = models.CharField(max_length=10, choices=TYPES)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    max_guests = models.PositiveSmallIntegerField(default=2)
    description = models.TextField(blank=True)
    amenities = models.CharField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True)
    inventory = models.PositiveSmallIntegerField(default=5, help_text='Rooms of this category available to sell')
    class Meta:
        unique_together = ('hotel', 'number')
        ordering = ['number']
    def __str__(self): return f'{self.hotel.name} / {self.number}'


class Booking(models.Model):
    PENDING, CONFIRMED, CANCELLED, COMPLETED = 'PENDING','CONFIRMED','CANCELLED','COMPLETED'
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='bookings')
    hotel = models.ForeignKey(Hotel, on_delete=models.PROTECT, related_name='bookings')
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name='bookings')
    check_in = models.DateField()
    check_out = models.DateField()
    guests = models.PositiveSmallIntegerField()
    rooms_count = models.PositiveSmallIntegerField(default=1)
    nights = models.PositiveSmallIntegerField()
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    tax = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=[(PENDING,'Pending payment'),(CONFIRMED,'Confirmed'),(CANCELLED,'Cancelled'),(COMPLETED,'Completed')], default=PENDING)
    created_at = models.DateTimeField(default=timezone.now)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    class Meta: ordering = ['-created_at']
    def __str__(self): return f'BK-{self.pk}'


class Payment(models.Model):
    PENDING, SUCCESS, FAILED, REFUNDED = 'PENDING','SUCCESS','FAILED','REFUNDED'
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=20)
    transaction_id = models.CharField(max_length=40, unique=True)
    status = models.CharField(max_length=10, choices=[(PENDING,'Pending'),(SUCCESS,'Success'),(FAILED,'Failed'),(REFUNDED,'Refunded')])
    paid_at = models.DateTimeField(null=True, blank=True)
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    refunded_at = models.DateTimeField(null=True, blank=True)


class Refund(models.Model):
    """Audit record for mock gateway refunds; swap gateway calls in production."""
    payment = models.OneToOneField(Payment, on_delete=models.PROTECT, related_name='refund')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reference = models.CharField(max_length=40, unique=True)
    status = models.CharField(max_length=20, default='PROCESSED')
    created_at = models.DateTimeField(auto_now_add=True)


class Review(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='reviews')
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    is_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: unique_together = ('hotel', 'customer')

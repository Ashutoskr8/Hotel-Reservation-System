from datetime import timedelta
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Hotel, Payment, Reservation, Room, User


class ReservationFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='guest', name='Guest', password='unused')
        self.hotel = Hotel.objects.create(manager=self.user, name='Demo Hotel', address='1 Main St', city='Bangalore', state_country='India', contact_number='9999999999', email='demo@example.com', status='ACTIVE')
        self.room = Room.objects.create(hotel=self.hotel, room_number='101', room_type='DELUXE', price_per_night=Decimal('3000.00'), max_guests=2)
        session = self.client.session; session['username'] = self.user.username; session.save()

    def test_date_overlap_is_rejected_and_total_is_calculated(self):
        start = timezone.localdate() + timedelta(days=5)
        response = self.client.post('/hotel/hotel_book_status', {'room_id': self.room.id, 'from_date': start.isoformat(), 'to_date': (start + timedelta(days=3)).isoformat(), 'guests': 2})
        self.assertRedirects(response, f'/hotel/bookings/1/payment/')
        booking = Reservation.objects.get()
        self.assertEqual(booking.subtotal, Decimal('9000.00'))
        self.assertEqual(booking.tax, Decimal('1620.00'))
        self.assertEqual(booking.total_amount, Decimal('10620.00'))
        self.client.post('/hotel/hotel_book_status', {'room_id': self.room.id, 'from_date': (start + timedelta(days=1)).isoformat(), 'to_date': (start + timedelta(days=4)).isoformat(), 'guests': 1})
        self.assertEqual(Reservation.objects.count(), 1)

    def test_django_superuser_can_use_application_login(self):
        get_user_model().objects.create_superuser('siteadmin', 'admin@example.com', 'StrongPass123!')
        response = self.client.post('/hotel/login', {'username': 'siteadmin', 'password': 'StrongPass123!'})
        self.assertRedirects(response, '/hotel/welcome', fetch_redirect_response=False)
        self.assertEqual(User.objects.get(username='siteadmin').role, 'ADMIN')

    def test_cancellation_marks_successful_payment_as_refunded(self):
        start = timezone.localdate() + timedelta(days=8)
        booking = Reservation.objects.create(customer=self.user, hotel=self.hotel, room=self.room, check_in=start, check_out=start + timedelta(days=2), guests=1, nights=2, subtotal=Decimal('6000.00'), tax=Decimal('1080.00'), total_amount=Decimal('7080.00'), status='CONFIRMED')
        Payment.objects.create(reservation=booking, amount=booking.total_amount, method='UPI', transaction_id='TEST-REFUND-001', status='SUCCESS')
        self.client.post(f'/hotel/bookings/{booking.id}/cancel/')
        booking.refresh_from_db(); booking.payment.refresh_from_db()
        self.assertEqual(booking.status, 'CANCELLED')
        self.assertEqual(booking.payment.status, 'REFUNDED')
        self.assertEqual(booking.payment.refund_amount, Decimal('7080.00'))

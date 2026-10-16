from datetime import timedelta
from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from .models import Booking, Hotel, Payment, Profile, Refund, Room


class BookingWorkflowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('guest', password='StrongPass123!')
        Profile.objects.create(user=self.user, location='Bengaluru')
        self.hotel = Hotel.objects.create(manager=self.user, name='Test Stay', address='1 Test Road', city='Bengaluru', state_country='India', description='Test', contact_number='123', email='test@example.com', status='ACTIVE')
        self.room = Room.objects.create(hotel=self.hotel, number='1', room_type='DELUXE', price_per_night=Decimal('3000'), max_guests=2, inventory=1)
        self.client.force_login(self.user)

    def test_login_is_required(self):
        self.client.logout(); response = self.client.get('/home/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_reservation_form_disallows_past_dates_in_browser_and_server(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        response = self.client.get(f'/rooms/{self.room.id}/reserve/')
        self.assertContains(response, f'min="{timezone.localdate():%Y-%m-%d}"')

        response = self.client.post(f'/rooms/{self.room.id}/reserve/', {
            'check_in': yesterday,
            'check_out': timezone.localdate() + timedelta(days=1),
            'guests': 1,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Check-in cannot be in the past.')

    def test_overlap_is_prevented_and_successful_payment_refunds(self):
        start = timezone.localdate() + timedelta(days=5)
        response = self.client.post(f'/rooms/{self.room.id}/reserve/', {'check_in':start, 'check_out':start + timedelta(days=3), 'guests':2})
        self.assertRedirects(response, '/bookings/1/pay/')
        booking = Booking.objects.get(); self.assertEqual(booking.total, Decimal('10620.00'))
        self.client.post(f'/rooms/{self.room.id}/reserve/', {'check_in':start + timedelta(days=1), 'check_out':start + timedelta(days=4), 'guests':2})
        self.assertEqual(Booking.objects.count(), 1)
        self.client.post(f'/bookings/{booking.id}/pay/', {'method':'UPI'})
        self.client.post(f'/bookings/{booking.id}/cancel/')
        booking.refresh_from_db(); booking.payment.refresh_from_db()
        self.assertEqual(booking.status, Booking.CANCELLED)
        self.assertEqual(booking.payment.status, Payment.REFUNDED)

    def test_paid_booking_can_be_cancelled_on_its_check_in_date(self):
        today = timezone.localdate()
        booking = Booking.objects.create(
            customer=self.user,
            hotel=self.hotel,
            room=self.room,
            check_in=today,
            check_out=today + timedelta(days=1),
            guests=1,
            nights=1,
            subtotal=Decimal('3000.00'),
            tax=Decimal('540.00'),
            total=Decimal('3540.00'),
            status=Booking.CONFIRMED,
        )
        Payment.objects.create(
            booking=booking,
            amount=booking.total,
            method='UPI',
            transaction_id='TEST-SAME-DAY-REFUND',
            status=Payment.SUCCESS,
        )

        response = self.client.post(f'/bookings/{booking.id}/cancel/')

        self.assertRedirects(response, '/bookings/')
        booking.refresh_from_db()
        booking.payment.refresh_from_db()
        self.assertEqual(booking.status, Booking.CANCELLED)
        self.assertEqual(booking.payment.status, Payment.REFUNDED)
        self.assertEqual(booking.payment.refund_amount, Decimal('3540.00'))
        self.assertTrue(Refund.objects.filter(payment=booking.payment, amount=Decimal('3540.00')).exists())

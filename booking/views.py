from datetime import date
from decimal import Decimal
from uuid import uuid4
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db import transaction
from django.db.models import Q, Sum
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .forms import BookingForm, SignUpForm
from .models import Booking, Hotel, Payment, Profile, Refund, Review, Room


def welcome(request):
    """Public entry point; every booking route remains protected by login_required."""
    return redirect('booking:home') if request.user.is_authenticated else render(request, 'booking/welcome.html')

def signup(request):
    if request.user.is_authenticated: return redirect('booking:home')
    form = SignUpForm(request.POST or None)
    if request.method == 'POST' and form.is_valid(): login(request, form.save()); return redirect('booking:home')
    return render(request, 'booking/signup.html', {'form': form})
def user_login(request):
    if request.user.is_authenticated: return redirect('booking:home')
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid(): login(request, form.get_user()); return redirect('booking:home')
    return render(request, 'booking/login.html', {'form': form})
def user_logout(request): logout(request); return redirect('booking:login')

@login_required
def home(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    hotels = Hotel.objects.filter(status=Hotel.ACTIVE)
    if profile.location: hotels = hotels.filter(Q(city__icontains=profile.location) | Q(state_country__icontains=profile.location))
    return render(request, 'booking/home.html', {'profile': profile, 'hotels': hotels[:10], 'recent': request.user.bookings.all()[:4]})


@login_required
def save_location(request):
    if request.method == 'POST':
        profile, _ = Profile.objects.get_or_create(user=request.user)
        location = request.POST.get('location', '').strip()
        if location:
            profile.location = location[:100]
            profile.save(update_fields=['location'])
            messages.success(request, f'Location set to {profile.location}.')
    return redirect('booking:home')


@login_required
def profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        request.user.first_name = request.POST.get('name', '').strip()[:30]
        request.user.email = request.POST.get('email', '').strip()[:254]
        request.user.save(update_fields=['first_name', 'email'])
        profile.phone = request.POST.get('phone', '').strip()[:20]
        profile.location = request.POST.get('location', '').strip()[:100]
        profile.save(update_fields=['phone', 'location'])
        messages.success(request, 'Profile updated.')
        return redirect('booking:profile')
    return render(request, 'booking/profile.html', {'profile': profile})

@login_required
def hotel_list(request):
    hotels = Hotel.objects.filter(status=Hotel.ACTIVE).prefetch_related('rooms')
    q, room_type = request.GET.get('location','').strip(), request.GET.get('room_type','')
    if q: hotels = hotels.filter(Q(city__icontains=q) | Q(state_country__icontains=q))
    if room_type: hotels = hotels.filter(rooms__room_type=room_type, rooms__is_active=True).distinct()
    return render(request, 'booking/hotel_list.html', {'hotels':hotels, 'types':Room.TYPES, 'searched_location': q})

@login_required
def hotel_detail(request, hotel_id):
    hotel=get_object_or_404(Hotel, pk=hotel_id, status=Hotel.ACTIVE)
    return render(request,'booking/hotel_detail.html',{'hotel':hotel, 'rooms':hotel.rooms.filter(is_active=True)})

@login_required
def reserve(request, room_id):
    room=get_object_or_404(Room, pk=room_id, is_active=True, hotel__status=Hotel.ACTIVE)
    form=BookingForm(request.POST or None, room=room)
    if request.method == 'POST' and form.is_valid():
        data=form.cleaned_data
        with transaction.atomic():
            booked = Booking.objects.select_for_update().filter(room=room, status__in=[Booking.PENDING,Booking.CONFIRMED], check_in__lt=data['check_out'], check_out__gt=data['check_in']).aggregate(total=Sum('rooms_count'))['total'] or 0
            if booked + data['rooms_count'] > room.inventory: form.add_error(None, 'That room category is unavailable for part of these dates. Choose different dates.')
            else:
                nights=(data['check_out']-data['check_in']).days; subtotal=room.price_per_night*nights*data['rooms_count']; tax=subtotal*Decimal('0.18')
                booking=Booking.objects.create(customer=request.user,hotel=room.hotel,room=room,check_in=data['check_in'],check_out=data['check_out'],guests=data['guests'],rooms_count=data['rooms_count'],nights=nights,subtotal=subtotal,tax=tax,total=subtotal+tax)
                return redirect('booking:pay', booking_id=booking.id)
    return render(request,'booking/reserve.html',{'room':room,'form':form})

@login_required
def pay(request, booking_id):
    booking=get_object_or_404(Booking,pk=booking_id,customer=request.user)
    if request.method == 'POST' and booking.status == Booking.PENDING:
        Payment.objects.update_or_create(booking=booking,defaults={'amount':booking.total,'method':request.POST.get('method','UPI'),'transaction_id':'TXN-'+uuid4().hex[:12].upper(),'status':Payment.SUCCESS,'paid_at':timezone.now()})
        booking.status=Booking.CONFIRMED; booking.save(update_fields=['status']); messages.success(request, 'Payment successful. Your reservation is confirmed.'); return redirect('booking:confirmation', booking_id=booking.id)
    return render(request,'booking/pay.html',{'booking':booking})

@login_required
def booking_list(request): return render(request,'booking/bookings.html',{'bookings':request.user.bookings.select_related('hotel','room','payment')})

@login_required
def confirmation(request, booking_id):
    booking = get_object_or_404(Booking.objects.select_related('hotel', 'room', 'payment'), pk=booking_id, customer=request.user)
    return render(request, 'booking/confirmation.html', {'booking': booking})

@login_required
def cancel(request, booking_id):
    booking=get_object_or_404(Booking,pk=booking_id,customer=request.user)
    if request.method != 'POST': return redirect('booking:booking_list')
    if booking.status not in [Booking.PENDING,Booking.CONFIRMED]: messages.error(request,'This booking has already been cancelled or completed.')
    else:
        booking.status=Booking.CANCELLED; booking.cancelled_at=timezone.now(); booking.save(update_fields=['status','cancelled_at'])
        if hasattr(booking,'payment') and booking.payment.status == Payment.SUCCESS:
            booking.payment.status=Payment.REFUNDED; booking.payment.refund_amount=booking.payment.amount; booking.payment.refunded_at=timezone.now(); booking.payment.save(update_fields=['status','refund_amount','refunded_at'])
            Refund.objects.update_or_create(payment=booking.payment, defaults={'amount': booking.payment.amount, 'reference': 'RFD-'+uuid4().hex[:12].upper(), 'status': 'PROCESSED'})
            messages.success(request, f'Booking cancelled. ₹{booking.payment.amount} refund processed in the mock payment gateway.')
        else: messages.success(request,'Booking cancelled. No payment was collected.')
    return redirect('booking:booking_list')

@login_required
def review(request, hotel_id):
    hotel=get_object_or_404(Hotel,pk=hotel_id)
    if request.method == 'POST' and Booking.objects.filter(customer=request.user,hotel=hotel,status=Booking.COMPLETED).exists():
        Review.objects.update_or_create(hotel=hotel,customer=request.user,defaults={'rating':request.POST['rating'],'comment':request.POST['comment']}); messages.success(request,'Review saved.')
    return redirect('booking:hotel_detail',hotel_id=hotel.id)

@login_required
def manager_dashboard(request):
    if not (request.user.is_superuser or getattr(request.user,'booking_profile',None) and request.user.booking_profile.role == Profile.MANAGER): return HttpResponseForbidden('Manager access required.')
    hotels=Hotel.objects.filter(manager=request.user) if not request.user.is_superuser else Hotel.objects.all()
    return render(request,'booking/manager.html',{'hotels':hotels,'bookings':Booking.objects.filter(hotel__in=hotels).select_related('customer','room')})

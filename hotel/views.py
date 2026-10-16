from datetime import date
from decimal import Decimal
from uuid import uuid4
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .models import Hotel, Payment, Profile, Reservation, Review, Room, User

def current_user(request):
    return User.objects.filter(username=request.session.get('username')).first()
def require_login(request):
    user = current_user(request)
    if not user: messages.error(request, 'Please sign in to continue.')
    return user
def welcome(request):
    # The welcome/dashboard page is intentionally private.
    user = require_login(request)
    if not user: return redirect('user:login')
    return render(request, 'welcome.html', {'user': user})
def signup(request): return render(request, 'signup.html')
def store_user(request):
    if request.method != 'POST': return redirect('user:signup')
    username, password, name = request.POST.get('username','').strip(), request.POST.get('password',''), request.POST.get('name','').strip()
    if not username or not name or len(password) < 8: return render(request, 'signup.html', {'msg':'Use a name, username, and password of at least 8 characters.'})
    if User.objects.filter(username=username).exists(): return render(request, 'signup.html', {'msg':'That username is already in use.'})
    user = User.objects.create(username=username, name=name, password=make_password(password))
    Profile.objects.create(username=user, location=request.POST.get('location', '').strip())
    messages.success(request, 'Account created. Please sign in.'); return redirect('user:login')
def login(request):
    if request.method == 'GET': return render(request, 'login.html')
    username, password = request.POST.get('username','').strip(), request.POST.get('password','')
    user = User.objects.filter(username=username).first()
    valid = user and (check_password(password, user.password) if user.password.startswith('pbkdf2_') else password == user.password)
    # Django admin accounts live in auth_user, whereas this project has a legacy
    # hotel.User table.  Create the linked application admin on first sign-in.
    if not valid and not user:
        django_user = authenticate(request, username=username, password=password)
        if django_user and django_user.is_superuser:
            user = User.objects.create(
                username=username,
                name=django_user.get_full_name() or django_user.username,
                password=make_password(password),
                role='ADMIN',
            )
            valid = True
    if not valid: return render(request, 'login.html', {'msg':'Incorrect username or password.'})
    if not user.password.startswith('pbkdf2_'): user.password = make_password(password); user.save(update_fields=['password'])
    request.session.cycle_key(); request.session['username'] = user.username
    return redirect('user:welcome')
def homepage(request):
    user = require_login(request)
    if not user: return redirect('user:login')
    profile, _ = Profile.objects.get_or_create(username=user)
    nearby_hotels = Hotel.objects.filter(status='ACTIVE')
    if profile.location:
        nearby_hotels = nearby_hotels.filter(Q(city__icontains=profile.location) | Q(state_country__icontains=profile.location))
    return render(request, 'homepage.html', {'user':user, 'profile':profile, 'recent_bookings':user.reservations.all()[:5], 'nearby_hotels':nearby_hotels[:6]})
def profile(request):
    user = require_login(request)
    if not user: return redirect('user:login')
    profile, _ = Profile.objects.get_or_create(username=user)
    return render(request, 'profile.html', {'profile':profile, 'user':user})
def profile_save(request):
    user = require_login(request)
    if not user or request.method != 'POST': return redirect('user:profile')
    profile, _ = Profile.objects.get_or_create(username=user)
    for field in ('fathers_name','mothers_name','email','phone'): setattr(profile, field, request.POST.get(field,'').strip() or 'not filled')
    profile.location = request.POST.get('location', '').strip()
    profile.save(); messages.success(request, 'Profile updated.'); return redirect('user:profile')

def hotel_list(request):
    if not require_login(request): return redirect('user:login')
    hotels = Hotel.objects.filter(status='ACTIVE').prefetch_related('rooms','reviews')
    city, room_type, max_price = request.GET.get('location','').strip(), request.GET.get('room_type',''), request.GET.get('max_price','')
    if city: hotels = hotels.filter(Q(city__icontains=city)|Q(state_country__icontains=city))
    if room_type: hotels = hotels.filter(rooms__room_type=room_type, rooms__is_active=True).distinct()
    if max_price:
        try: hotels = hotels.filter(rooms__price_per_night__lte=Decimal(max_price)).distinct()
        except Exception: messages.error(request, 'Price filter must be a number.')
    return render(request, 'hotel_list.html', {'hotels':hotels, 'room_types':Room.ROOM_TYPES, 'filters':request.GET})
def hotel_detail(request, hotel_id):
    hotel = get_object_or_404(Hotel.objects.prefetch_related('rooms','reviews__customer'), pk=hotel_id, status='ACTIVE')
    return render(request, 'hotel_detail.html', {'hotel':hotel, 'rooms':hotel.rooms.filter(is_active=True)})
def hotel_book(request, room_id=None):
    user = require_login(request)
    if not user: return redirect('user:login')
    room = get_object_or_404(Room, pk=room_id, is_active=True) if room_id else None
    return render(request, 'hotel_book.html', {'room':room, 'today':date.today().isoformat()})
def hotel_book_status(request):
    user = require_login(request)
    if not user or request.method != 'POST': return redirect('user:hotel_list')
    try:
        room = get_object_or_404(Room, pk=request.POST.get('room_id'), is_active=True, hotel__status='ACTIVE')
        check_in, check_out, guests = date.fromisoformat(request.POST['from_date']), date.fromisoformat(request.POST['to_date']), int(request.POST.get('guests',1))
        if check_in < date.today() or check_out <= check_in: raise ValueError('Choose valid future check-in and check-out dates.')
        if guests < 1 or guests > room.max_guests: raise ValueError(f'This room accepts 1–{room.max_guests} guests.')
        with transaction.atomic():
            conflict = Reservation.objects.select_for_update().filter(room=room,status__in=['PENDING','CONFIRMED'],check_in__lt=check_out,check_out__gt=check_in).exists()
            if conflict: raise ValueError('This room is unavailable for part of those dates.')
            nights=(check_out-check_in).days; subtotal=room.price_per_night*nights; tax=subtotal*Decimal('0.18')
            booking=Reservation.objects.create(customer=user,hotel=room.hotel,room=room,check_in=check_in,check_out=check_out,guests=guests,nights=nights,subtotal=subtotal,tax=tax,total_amount=subtotal+tax)
        return redirect('user:payment', booking_id=booking.pk)
    except (ValueError, KeyError) as error:
        messages.error(request, str(error)); return redirect(request.META.get('HTTP_REFERER','/hotel/hotels/'))
def payment(request, booking_id):
    user = require_login(request)
    if not user: return redirect('user:login')
    booking=get_object_or_404(Reservation,pk=booking_id,customer=user)
    if request.method == 'POST':
        if booking.status == 'CANCELLED': messages.error(request,'Cancelled bookings cannot be paid.'); return redirect('user:my_bookings')
        Payment.objects.update_or_create(reservation=booking,defaults={'amount':booking.total_amount,'method':request.POST.get('method','UPI'),'transaction_id':'TXN-'+uuid4().hex[:12].upper(),'status':'SUCCESS','paid_at':timezone.now()})
        booking.status='CONFIRMED'; booking.save(update_fields=['status']); messages.success(request,'Payment successful. Your booking is confirmed.')
        return redirect('user:booking_confirmation',booking_id=booking.pk)
    return render(request,'payment.html',{'booking':booking,'methods':Payment.METHODS})
def booking_confirmation(request, booking_id):
    user=require_login(request)
    if not user: return redirect('user:login')
    return render(request,'booking_confirmation.html',{'booking':get_object_or_404(Reservation.objects.select_related('room','hotel'),pk=booking_id,customer=user)})
def hotel_book_history(request):
    user=require_login(request)
    if not user: return redirect('user:login')
    return render(request,'hotel_book_history.html',{'bookings':user.reservations.select_related('hotel','room')})
def cancel_booking(request, booking_id):
    user=require_login(request)
    if not user or request.method != 'POST': return redirect('user:my_bookings')
    booking=get_object_or_404(Reservation,pk=booking_id,customer=user)
    if booking.status not in ['PENDING','CONFIRMED'] or booking.check_in <= date.today(): messages.error(request,'This booking can no longer be cancelled.')
    else:
        booking.status='CANCELLED'; booking.cancelled_at=timezone.now(); booking.save(update_fields=['status','cancelled_at'])
        if hasattr(booking,'payment') and booking.payment.status == 'SUCCESS':
            booking.payment.status='REFUNDED'; booking.payment.refund_amount=booking.payment.amount; booking.payment.refunded_at=timezone.now()
            booking.payment.save(update_fields=['status','refund_amount','refunded_at'])
            messages.success(request, f'Booking cancelled. Refund of ₹{booking.payment.amount} has been processed in the mock payment system.')
        else:
            messages.success(request,'Booking cancelled. No payment was collected, so no refund is needed.')
    return redirect('user:my_bookings')
def add_review(request, hotel_id):
    user=require_login(request)
    if not user or request.method != 'POST': return redirect('user:hotel_detail',hotel_id=hotel_id)
    hotel=get_object_or_404(Hotel,pk=hotel_id)
    if not Reservation.objects.filter(customer=user,hotel=hotel,status='COMPLETED').exists(): messages.error(request,'You can review a hotel after a completed stay.')
    else:
        try: Review.objects.update_or_create(hotel=hotel,customer=user,defaults={'rating':int(request.POST['rating']),'comment':request.POST['comment'].strip()}); messages.success(request,'Review saved.')
        except (ValueError,KeyError): messages.error(request,'Please enter a rating from 1 to 5.')
    return redirect('user:hotel_detail',hotel_id=hotel_id)
def logout(request): request.session.flush(); return redirect('user:login')
def about(request): return render(request,'about.html')
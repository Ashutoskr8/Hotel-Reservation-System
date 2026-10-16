from django.urls import path
from hotel import views
app_name='user'
urlpatterns = [
    path("welcome",views.welcome,name='welcome'),
    path("signup",views.signup,name='signup'),
    path("store_user",views.store_user,name='store_user'),
    path("login",views.login,name='login'),
    path("homepage",views.homepage,name='homepage'),
    path("profile",views.profile,name='profile'),
    path("profile_save",views.profile_save,name='profile_save'),
    path("hotel_book",views.hotel_book,name='hotel_book'),
    path("hotels/",views.hotel_list,name='hotel_list'),
    path("hotels/<int:hotel_id>/",views.hotel_detail,name='hotel_detail'),
    path("rooms/<int:room_id>/book/",views.hotel_book,name='room_book'),
    path("hotel_book_status",views.hotel_book_status,name='hotel_book_status'),
    path("bookings/<int:booking_id>/payment/",views.payment,name='payment'),
    path("bookings/<int:booking_id>/confirmation/",views.booking_confirmation,name='booking_confirmation'),
    path("hotel_book_history",views.hotel_book_history,name='hotel_book_history'),
    path("my-bookings/",views.hotel_book_history,name='my_bookings'),
    path("bookings/<int:booking_id>/cancel/",views.cancel_booking,name='cancel_booking'),
    path("hotels/<int:hotel_id>/review/",views.add_review,name='add_review'),
    path("logout",views.logout,name='logout'),
    path("about",views.about,name='about'),
]

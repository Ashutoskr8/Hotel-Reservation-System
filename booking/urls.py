from django.urls import path
from . import views

app_name = 'booking'
urlpatterns = [
    path('', views.welcome, name='welcome'), path('easystay', views.welcome, name='easystay'), path('home/', views.home, name='home'), path('signup/', views.signup, name='signup'), path('login/', views.user_login, name='login'), path('logout/', views.user_logout, name='logout'),
    path('hotels/', views.hotel_list, name='hotel_list'), path('hotels/<int:hotel_id>/', views.hotel_detail, name='hotel_detail'), path('rooms/<int:room_id>/reserve/', views.reserve, name='reserve'),
    path('bookings/', views.booking_list, name='booking_list'), path('bookings/<int:booking_id>/pay/', views.pay, name='pay'), path('bookings/<int:booking_id>/confirmation/', views.confirmation, name='confirmation'), path('bookings/<int:booking_id>/cancel/', views.cancel, name='cancel'),
    path('profile/', views.profile, name='profile'), path('location/', views.save_location, name='save_location'),
    path('hotels/<int:hotel_id>/review/', views.review, name='review'), path('manager/', views.manager_dashboard, name='manager_dashboard'),
]

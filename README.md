# Easystay Hotel Reservation System

Full-stack Django hotel reservation application with secure session authentication, hotel search, browser location detection, booking totals, mock payments/refunds, and reservation history.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install "Django>=5.1,<5.2"
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/`. Create an account through Sign up; passwords use Django's PBKDF2 password hashing. The seed migration adds 10+ Bengaluru hotels plus additional cities. The seed manager username is `hotel_manager` (set its password with `python manage.py changepassword hotel_manager` if you need to administer it).

## Main routes / application API

Server-rendered endpoints: `/`, `/signup/`, `/login/`, `/home/`, `/hotels/`, `/hotels/<id>/`, `/rooms/<id>/reserve/`, `/bookings/`, `/profile/`, and `/location/`. POST actions are CSRF-protected and require authenticated sessions where applicable.

Models: `Profile`, `Hotel`, `Room` (including inventory), `Booking`, `Payment`, `Refund`, and `Review`. Foreign keys connect bookings to users, hotels, rooms, and payments; one payment/refund audit record belongs to each booking/payment.

## Payments and deployment

The supplied payment flow is deliberately a mock gateway: it stores no card data, generates a transaction reference, and writes a refund record on eligible cancellation. For Stripe/Razorpay, replace the mock section in `booking/views.py:pay` and `cancel` with the provider's server-side API calls, keep their secrets outside source control, and validate webhook signatures before changing payment states.

Set the variables in `.env.example` via your host's environment configuration. Use PostgreSQL and `DJANGO_DEBUG=false` in production, configure HTTPS/secure cookies, and set real allowed hosts.

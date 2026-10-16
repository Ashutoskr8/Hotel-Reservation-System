from datetime import date
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Booking, Profile


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, label='Full name')
    email = forms.EmailField()
    location = forms.CharField(max_length=100, label='Your city / preferred location', help_text='Example: Bengaluru')
    phone = forms.CharField(max_length=20, required=False)
    class Meta:
        model = User
        fields = ('username', 'first_name', 'email', 'location', 'phone', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Django 5.1 adds this admin-oriented choice to UserCreationForm.
        # Public registrations always use a password, so it is not a useful
        # choice on this form.
        self.fields.pop('usable_password', None)

    def save(self, commit=True):
        user = super().save(commit=False); user.first_name = self.cleaned_data['first_name']; user.email = self.cleaned_data['email']
        if commit:
            user.save(); Profile.objects.create(user=user, location=self.cleaned_data['location'], phone=self.cleaned_data['phone'])
        return user


class BookingForm(forms.Form):
    check_in = forms.DateField(widget=forms.DateInput(attrs={'type':'date'}))
    check_out = forms.DateField(widget=forms.DateInput(attrs={'type':'date'}))
    guests = forms.IntegerField(min_value=1)
    rooms_count = forms.IntegerField(min_value=1, initial=1, required=False, label='Number of rooms')
    def __init__(self, *args, room=None, **kwargs):
        self.room = room
        super().__init__(*args, **kwargs)
        # Keep invalid dates out of the date picker as well as validating them
        # on the server.  The server-side checks below remain authoritative.
        today = date.today().isoformat()
        self.fields['check_in'].widget.attrs['min'] = today
        self.fields['check_out'].widget.attrs['min'] = today
    def clean(self):
        data = super().clean(); data['rooms_count'] = data.get('rooms_count') or 1; check_in, check_out, guests = data.get('check_in'), data.get('check_out'), data.get('guests')
        if check_in and check_in < date.today(): self.add_error('check_in', 'Check-in cannot be in the past.')
        if check_in and check_out and check_out <= check_in: self.add_error('check_out', 'Check-out must be after check-in.')
        if guests and self.room and guests > self.room.max_guests * data.get('rooms_count', 1): self.add_error('guests', f'Choose more rooms: each room supports up to {self.room.max_guests} guests.')
        if data.get('rooms_count') and self.room and data['rooms_count'] > self.room.inventory: self.add_error('rooms_count', 'That many rooms are not available in this category.')
        return data

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Appointment, Patient ,Doctor , Department

class PatientRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class AppointmentForm(forms.ModelForm):

    class Meta:

        model = Appointment

        fields = [
            'doctor',
            'date',
            'time',
            'symptoms'
        ]


        widgets = {

            'date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control'
                }
            ),


            'time': forms.TimeInput(
                attrs={
                    'type': 'time',
                    'class': 'form-control'
                }
            ),


            'symptoms': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 5,
                    'placeholder':
                    'Describe your symptoms...'
                }
            ),


            'doctor': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            )

        }

class DoctorCreationForm(UserCreationForm):

    email = forms.EmailField(
        required=True
    )

    name = forms.CharField(
        max_length=100
    )

    department = forms.ModelChoiceField(
        queryset=Department.objects.all()
    )

    qualification = forms.CharField(
        max_length=200
    )

    experience = forms.IntegerField(
        min_value=0
    )

    fee = forms.DecimalField(
        max_digits=8,
        decimal_places=2,
        min_value=0
    )

    image = forms.ImageField(
        required=False
    )

    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                'rows': 4
            }
        )
    )

    location = forms.CharField(
        max_length=200,
        required=False
    )

    languages = forms.CharField(
        max_length=200,
        required=False
    )

    available_days = forms.CharField(
        max_length=200,
        required=False
    )

    rating = forms.DecimalField(
        max_digits=2,
        decimal_places=1,
        min_value=0,
        max_value=5,
        initial=5.0
    )

    class Meta:

        model = User

        fields = [
            'username',
            'email',
            'password1',
            'password2',
        ]
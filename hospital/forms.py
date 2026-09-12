from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Appointment, Patient ,Doctor , Department

class PatientRegistrationForm(UserCreationForm):

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Email address'
            }
        )
    )

    full_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Full name'
            }
        )
    )

    date_of_birth = forms.DateField(
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control'
            }
        )
    )

    gender = forms.ChoiceField(
        choices=Patient._meta.get_field(
            'gender'
        ).choices,
        widget=forms.Select(
            attrs={
                'class': 'form-select'
            }
        )
    )

    phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Phone number'
            }
        )
    )

    address = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Home address'
            }
        )
    )

    blood_group = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Example: O+'
            }
        )
    )


    class Meta:

        model = User

        fields = [
            'username',
            'email',
            'password1',
            'password2',
        ]


    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Username'
        })

        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })

        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })

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
        
class PatientProfileForm(forms.ModelForm):

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control'
            }
        )
    )

    class Meta:

        model = Patient

        fields = [
            'full_name',
            'date_of_birth',
            'gender',
            'phone',
            'address',
            'blood_group',
        ]

        widgets = {

            'full_name': forms.TextInput(
                attrs={
                    'class': 'form-control'
                }
            ),

            'date_of_birth': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control'
                }
            ),

            'gender': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),

            'phone': forms.TextInput(
                attrs={
                    'class': 'form-control'
                }
            ),

            'address': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4
                }
            ),

            'blood_group': forms.TextInput(
                attrs={
                    'class': 'form-control'
                }
            ),
        }


    def __init__(self, *args, **kwargs):

        user = kwargs.pop(
            'user',
            None
        )

        super().__init__(
            *args,
            **kwargs
        )

        if user:

            self.fields[
                'email'
            ].initial = user.email

            self.user = user


    def save(self, commit=True):

        patient = super().save(
            commit=False
        )

        if hasattr(
            self,
            'user'
        ):

            self.user.email = (
                self.cleaned_data['email']
            )

            if commit:

                self.user.save(
                    update_fields=[
                        'email'
                    ]
                )

        if commit:

            patient.save()

        return patient
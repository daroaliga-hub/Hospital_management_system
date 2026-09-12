from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.views.decorators.http import require_POST
from .decorators import doctor_required, patient_required
from django.contrib.auth.models import Group
from .models import Department, Doctor, Patient, Appointment
from .forms import PatientRegistrationForm, AppointmentForm ,DoctorCreationForm, PatientProfileForm

def home(request):
    departments = Department.objects.all()[:6]
    return render(
    request,
    'public/home.html',
    {
        'departments': departments
    }
)

def doctor_list(request):

    doctors = Doctor.objects.all()


    search = request.GET.get(
        'search'
    )

    department = request.GET.get(
        'department'
    )


    if search:

        doctors = doctors.filter(
            name__icontains=search
        )


    if department:

        doctors = doctors.filter(
            department__id=department
        )


    departments = Department.objects.all()


    return render(
        request,
        'public/doctor_list.html',
        {
            'doctors': doctors,
            'departments': departments
        }
    )
def doctor_profile(request, id):

    doctor = get_object_or_404(
        Doctor,
        id=id
    )


    return render(
        request,
        'public/doctor_profile.html',
        {
            'doctor': doctor
        }
    )
    
def register(request):

    if request.user.is_authenticated:
        return login_redirect(request)


    if request.method == 'POST':

        form = PatientRegistrationForm(
            request.POST
        )


        if form.is_valid():

            with transaction.atomic():

                # -------------------------
                # CREATE USER ACCOUNT
                # -------------------------

                user = form.save(
                    commit=False
                )

                user.email = form.cleaned_data[
                    'email'
                ]

                user.save()


                # -------------------------
                # ASSIGN PATIENT ROLE
                # -------------------------

                patient_group, created = (
                    Group.objects.get_or_create(
                        name='Patient'
                    )
                )

                user.groups.add(
                    patient_group
                )


                # -------------------------
                # CREATE PATIENT PROFILE
                # -------------------------

                Patient.objects.create(

                    user=user,

                    full_name=form.cleaned_data[
                        'full_name'
                    ],

                    date_of_birth=form.cleaned_data[
                        'date_of_birth'
                    ],

                    gender=form.cleaned_data[
                        'gender'
                    ],

                    phone=form.cleaned_data[
                        'phone'
                    ],

                    address=form.cleaned_data[
                        'address'
                    ],

                    blood_group=form.cleaned_data[
                        'blood_group'
                    ],
                )


            login(
                request,
                user
            )


            messages.success(
                request,
                "Registration successful!"
            )


            return redirect(
                'dashboard'
            )


    else:

        form = PatientRegistrationForm()


    return render(
        request,
        'authentication/register.html',
        {
            'form': form
        }
    )

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request,user)
            return login_redirect(request)

        messages.error(request, "Invalid credentials")
    return render(
    request,
    'authentication/login.html'
)

@login_required
@patient_required
def dashboard(request):

    patient = get_object_or_404(
        Patient,
        user=request.user
    )


    appointments = Appointment.objects.filter(
        patient=patient
    ).order_by(
        '-date',
        '-time'
    )


    upcoming = appointments.filter(
        status__in=[
            'pending',
            'confirmed'
        ]
    )[:3]


    completed = appointments.filter(
        status='completed'
    )[:5]


    return render(
        request,
        'patient/dashboard.html',
        {
            'patient': patient,
            'appointments': appointments,
            'upcoming': upcoming,
            'completed': completed
        }
    )

@login_required
@patient_required
def book_appointment(request):

    selected_doctor = request.GET.get(
        'doctor'
    )


    if request.method == 'POST':

        form = AppointmentForm(
            request.POST
        )


        if form.is_valid():

            appointment = form.save(
                commit=False
            )


            patient, created = Patient.objects.get_or_create(
                user=request.user,
                defaults={
                    "full_name": request.user.username
                }
            )

            appointment.patient = patient


            appointment.department = (
                appointment.doctor.department
            )


            existing = Appointment.objects.filter(

                doctor=appointment.doctor,

                date=appointment.date,

                time=appointment.time,

                status__in=[
                    'pending',
                    'confirmed'
                ]

            ).exists()



            if existing:

                messages.error(
                    request,
                    "This doctor is not available at this time."
                )


            else:

                appointment.save()


                messages.success(
                    request,
                    "Appointment booked successfully!"
                )


                return redirect(
                    'dashboard'
                )



    else:

        form = AppointmentForm()



        if selected_doctor:

            form.fields[
                'doctor'
            ].initial = selected_doctor



    return render(

        request,

        'book_appointment.html',

        {
            'form': form
        }

    )

@login_required
def user_logout(request):
    logout(request)
    return redirect('home')

@login_required
@doctor_required
def doctor_dashboard(request):

    try:

        doctor = request.user.doctor


    except Doctor.DoesNotExist:

        messages.error(
            request,
            "You are not registered as a doctor."
        )

        return redirect('home')



    appointments = Appointment.objects.filter(
        doctor=doctor
    ).order_by(
        '-date',
        '-time'
    )


    pending = appointments.filter(
        status='pending'
    )


    confirmed = appointments.filter(
        status='confirmed'
    )


    completed = appointments.filter(
        status='completed'
    )


    return render(
        request,
        'doctor/dashboard.html',
        {
            'doctor': doctor,
            'appointments': appointments,
            'pending': pending,
            'confirmed': confirmed,
            'completed': completed,
        }
    )

@login_required
@doctor_required
@require_POST
def update_appointment_status(
    request,
    appointment_id,
    status
):

    doctor = get_object_or_404(
        Doctor,
        user=request.user
    )

    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        doctor=doctor
    )

    allowed_transitions = {

        'pending': [
            'confirmed',
            'cancelled'
        ],

        'confirmed': [
            'completed',
            'cancelled'
        ],

        'completed': [],

        'cancelled': [],
    }


    allowed_statuses = allowed_transitions.get(
        appointment.status,
        []
    )


    if status not in allowed_statuses:

        messages.error(
            request,
            "This appointment status change is not allowed."
        )

        return redirect(
            'doctor_dashboard'
        )


    appointment.status = status

    appointment.save(
        update_fields=['status']
    )


    messages.success(
        request,
        f"Appointment {status}."
    )


    return redirect(
        'doctor_dashboard'
    )
@login_required
@doctor_required
def add_medical_notes(
    request,
    appointment_id
):

    doctor = get_object_or_404(
        Doctor,
        user=request.user
    )

    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        doctor=doctor
    )


    if appointment.status not in [
        'confirmed',
        'completed'
    ]:

        messages.error(
            request,
            "Medical notes can only be added to confirmed or completed appointments."
        )

        return redirect(
            'doctor_dashboard'
        )


    if request.method == "POST":

        notes = request.POST.get(
            "medical_notes",
            ""
        ).strip()


        appointment.medical_notes = notes

        appointment.status = "completed"

        appointment.save(
            update_fields=[
                'medical_notes',
                'status'
            ]
        )


        messages.success(
            request,
            "Medical notes saved and appointment completed."
        )


        return redirect(
            'doctor_dashboard'
        )


    return render(
        request,
        'doctor/add_notes.html',
        {
            'appointment': appointment
        }
    )
def login_redirect(request):

    if request.user.is_superuser or request.user.is_staff:

        return redirect(
            'admin:index'
        )


    if request.user.groups.filter(
        name="Doctor"
    ).exists():

        return redirect(
            'doctor_dashboard'
        )


    if request.user.groups.filter(
        name="Patient"
    ).exists():

        return redirect(
            'dashboard'
        )


    return redirect(
        'home'
    )
    
@staff_member_required
def create_doctor(request):

    if request.method == "POST":

        form = DoctorCreationForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            with transaction.atomic():

                # -------------------------
                # CREATE LOGIN ACCOUNT
                # -------------------------

                user = form.save(
                    commit=False
                )

                user.email = form.cleaned_data[
                    'email'
                ]

                user.save()


                # -------------------------
                # ASSIGN DOCTOR ROLE
                # -------------------------

                doctor_group, created = (
                    Group.objects.get_or_create(
                        name="Doctor"
                    )
                )

                user.groups.add(
                    doctor_group
                )


                # -------------------------
                # CREATE DOCTOR PROFILE
                # -------------------------

                Doctor.objects.create(

                    user=user,

                    name=form.cleaned_data[
                        'name'
                    ],

                    department=form.cleaned_data[
                        'department'
                    ],

                    qualification=form.cleaned_data[
                        'qualification'
                    ],

                    experience=form.cleaned_data[
                        'experience'
                    ],

                    fee=form.cleaned_data[
                        'fee'
                    ],

                    image=form.cleaned_data.get(
                        'image'
                    ),

                    bio=form.cleaned_data.get(
                        'bio'
                    ),

                    location=form.cleaned_data.get(
                        'location'
                    ),

                    languages=form.cleaned_data.get(
                        'languages'
                    ),

                    available_days=form.cleaned_data.get(
                        'available_days'
                    ),

                    rating=form.cleaned_data[
                        'rating'
                    ],
                )


            messages.success(
                request,
                "Doctor account created successfully."
            )

            return redirect(
                'doctor_list'
            )

    else:

        form = DoctorCreationForm()


    return render(
        request,
        'management/create_doctor.html',
        {
            'form': form
        }
    )
@login_required
@patient_required
def patient_profile(request):

    patient = get_object_or_404(
        Patient,
        user=request.user
    )

    return render(
        request,
        'patient/profile.html',
        {
            'patient': patient
        }
    )
@login_required
@patient_required
def edit_patient_profile(request):

    patient = get_object_or_404(
        Patient,
        user=request.user
    )

    if request.method == 'POST':

        form = PatientProfileForm(
            request.POST,
            instance=patient,
            user=request.user
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Profile updated successfully."
            )

            return redirect(
                'patient_profile'
            )

    else:

        form = PatientProfileForm(
            instance=patient,
            user=request.user
        )

    return render(
        request,
        'patient/edit_profile.html',
        {
            'form': form,
            'patient': patient,
        }
    )
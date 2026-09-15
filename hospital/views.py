from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.views.decorators.http import require_POST
from .decorators import doctor_required, patient_required ,admin_required
from django.contrib.auth.models import Group
from .utils import doctor_is_available , get_available_time_slots,create_notification
from django.db.models import Count
from django.utils import timezone
from .models import Department, Doctor, Patient, Appointment, DoctorAvailability,Notification
from .forms import PatientRegistrationForm, AppointmentForm ,DoctorCreationForm, PatientProfileForm,DoctorAvailabilityForm
from datetime import datetime
from django.http import JsonResponse

def home(request):
    departments = Department.objects.all()[:6]
    return render(
    request,
    'public/home.html',
    {
        'departments': departments
    }
)
def services(request):

    return render(
        request,
        'public/services.html'
    )

def departments(request):

    departments = (
        Department.objects.annotate(
            doctor_count=Count(
                'doctor',
                distinct=True
            )
        )
        .order_by('name')
    )

    return render(
        request,
        'public/departments.html',
        {
            'departments': departments
        }
    )


def locations(request):

    return render(
        request,
        'public/locations.html'
    )


def about(request):

    return render(
        request,
        'public/about.html'
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

    selected_doctor_id = request.GET.get(
        'doctor'
    )


    patient = get_object_or_404(
        Patient,
        user=request.user
    )


    selected_doctor = None
    selected_date = None


    # -----------------------------------
    # POST
    # -----------------------------------

    if request.method == 'POST':

        doctor_id = request.POST.get(
            'doctor'
        )

        date_value = request.POST.get(
            'date'
        )


        if doctor_id:

            try:

                selected_doctor = (
                    Doctor.objects.get(
                        id=doctor_id
                    )
                )

            except Doctor.DoesNotExist:

                selected_doctor = None


        if date_value:

            try:

                selected_date = (
                    datetime.strptime(
                        date_value,
                        '%Y-%m-%d'
                    ).date()
                )

            except ValueError:

                selected_date = None


        form = AppointmentForm(
            request.POST,
            doctor=selected_doctor,
            appointment_date=selected_date
        )


        if form.is_valid():

            appointment = form.save(
                commit=False
            )


            appointment.patient = patient


            appointment.department = (
                appointment.doctor.department
            )


            # -----------------------------
            # DATE PROTECTION
            # -----------------------------

            if (
                appointment.date
                < timezone.localdate()
            ):

                messages.error(
                    request,
                    "You cannot book an appointment in the past."
                )


                return render(
                    request,
                    'book_appointment.html',
                    {
                        'form': form
                    }
                )


            # -----------------------------
            # SCHEDULE PROTECTION
            # -----------------------------

            if not doctor_is_available(
                appointment.doctor,
                appointment.date,
                appointment.time
            ):

                messages.error(
                    request,
                    "The doctor is not available at that date and time."
                )


                return render(
                    request,
                    'book_appointment.html',
                    {
                        'form': form
                    }
                )


            # -----------------------------
            # DOUBLE BOOKING PROTECTION
            # -----------------------------

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
                    "That appointment slot has just been booked. "
                    "Please select another time."
                )


            else:

                appointment.save()
                if appointment.doctor.user:

                    create_notification(
                        recipient=appointment.doctor.user,

                        notification_type='appointment_requested',

                        message=(
                            f"New appointment request from "
                            f"{appointment.patient.full_name} "
                            f"for {appointment.date} "
                            f"at {appointment.time.strftime('%H:%M')}."
                        ),

                        appointment=appointment
                    )


                messages.success(
                    request,
                    "Appointment booked successfully!"
                )


                return redirect(
                    'dashboard'
                )


    # -----------------------------------
    # GET
    # -----------------------------------

    else:

        initial = {}


        if selected_doctor_id:

            try:

                selected_doctor = (
                    Doctor.objects.get(
                        id=selected_doctor_id
                    )
                )

                initial[
                    'doctor'
                ] = selected_doctor


            except Doctor.DoesNotExist:

                selected_doctor = None


        form = AppointmentForm(
            initial=initial
        )


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

    doctor = get_object_or_404(
        Doctor,
        user=request.user
    )

    today = timezone.localdate()


    appointments = Appointment.objects.filter(
        doctor=doctor
    ).select_related(
        'patient',
        'department'
    )


    # -----------------------------------
    # TODAY
    # -----------------------------------

    today_appointments = appointments.filter(
        date=today
    ).exclude(
        status='cancelled'
    ).order_by(
        'time'
    )


    # -----------------------------------
    # PENDING REQUESTS
    # -----------------------------------

    pending = appointments.filter(
        status='pending',
        date__gte=today
    ).order_by(
        'date',
        'time'
    )


    # -----------------------------------
    # UPCOMING CONFIRMED
    # -----------------------------------

    upcoming = appointments.filter(
        status='confirmed',
        date__gt=today
    ).order_by(
        'date',
        'time'
    )[:5]


    # -----------------------------------
    # COMPLETED
    # -----------------------------------

    completed = appointments.filter(
        status='completed'
    ).order_by(
        '-date',
        '-time'
    )[:5]


    return render(
        request,
        'doctor/dashboard.html',
        {
            'doctor': doctor,
            'today': today,
            'today_appointments': today_appointments,
            'pending': pending,
            'upcoming': upcoming,
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
    if appointment.doctor.user:

        create_notification(
            recipient=appointment.doctor.user,

            notification_type='appointment_cancelled',

            message=(
                f"{appointment.patient.full_name} "
                f"cancelled the appointment scheduled "
                f"for {appointment.date} "
                f"at {appointment.time.strftime('%H:%M')}."
            ),

            appointment=appointment
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

        previous_status = appointment.status

        appointment.medical_notes = notes

        appointment.status = "completed"

        appointment.save(
            update_fields=[
                'medical_notes',
                'status'
            ]
        )
        if appointment.patient.user:

            if previous_status != 'completed':

                create_notification(
                    recipient=appointment.patient.user,

                    notification_type='appointment_completed',

                    message=(
                        f"Your appointment with "
                        f"Dr. {appointment.doctor.name} "
                        f"is complete. Medical notes "
                        f"are now available."
                    ),

                    appointment=appointment
                )


            else:

                create_notification(
                    recipient=appointment.patient.user,

                    notification_type='medical_notes_updated',

                    message=(
                        f"Dr. {appointment.doctor.name} "
                        f"updated the medical notes "
                        f"for your appointment."
                    ),

                    appointment=appointment
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
            'hospital_admin_dashboard'
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
@login_required
@patient_required
def appointment_detail(
    request,
    appointment_id
):

    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        patient__user=request.user
    )

    return render(
        request,
        'patient/appointment_detail.html',
        {
            'appointment': appointment
        }
    )
@login_required
@patient_required
@require_POST
def cancel_patient_appointment(
    request,
    appointment_id
):

    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        patient__user=request.user
    )


    if appointment.status not in [
        'pending',
        'confirmed'
    ]:

        messages.error(
            request,
            "This appointment can no longer be cancelled."
        )

        return redirect(
            'appointment_detail',
            appointment_id=appointment.id
        )


    appointment.status = 'cancelled'

    appointment.save(
        update_fields=[
            'status'
        ]
    )


    messages.success(
        request,
        "Appointment cancelled successfully."
    )


    return redirect(
        'appointment_detail',
        appointment_id=appointment.id
    )
@login_required
@doctor_required
def doctor_schedule(request):

    doctor = get_object_or_404(
        Doctor,
        user=request.user
    )


    if request.method == 'POST':

        form = DoctorAvailabilityForm(
            request.POST,
            doctor=doctor
        )


        if form.is_valid():

            availability = form.save(
                commit=False
            )

            availability.doctor = doctor

            availability.save()


            messages.success(
                request,
                "Availability added successfully."
            )


            return redirect(
                'doctor_schedule'
            )


    else:

        form = DoctorAvailabilityForm(
            doctor=doctor
        )


    schedules = DoctorAvailability.objects.filter(
        doctor=doctor
    )


    return render(
        request,
        'doctor/schedule.html',
        {
            'doctor': doctor,
            'form': form,
            'schedules': schedules,
        }
    )
@login_required
@doctor_required
@require_POST
def delete_doctor_availability(
    request,
    availability_id
):

    doctor = get_object_or_404(
        Doctor,
        user=request.user
    )


    availability = get_object_or_404(
        DoctorAvailability,
        id=availability_id,
        doctor=doctor
    )


    availability.delete()


    messages.success(
        request,
        "Availability removed."
    )


    return redirect(
        'doctor_schedule'
    )
@login_required
@patient_required
def appointment_slots(request):

    doctor_id = request.GET.get(
        'doctor'
    )

    date_value = request.GET.get(
        'date'
    )


    if not doctor_id or not date_value:

        return JsonResponse(
            {
                'slots': []
            }
        )


    try:

        doctor = Doctor.objects.get(
            id=doctor_id
        )


        appointment_date = (
            datetime.strptime(
                date_value,
                '%Y-%m-%d'
            ).date()
        )


    except (
        Doctor.DoesNotExist,
        ValueError
    ):

        return JsonResponse(
            {
                'slots': [],
                'error':
                'Invalid doctor or date.'
            },
            status=400
        )


    if (
        appointment_date
        < timezone.localdate()
    ):

        return JsonResponse(
            {
                'slots': [],
                'error':
                'Appointments cannot be booked in the past.'
            },
            status=400
        )


    slots = get_available_time_slots(
        doctor,
        appointment_date
    )


    slot_data = []


    for slot in slots:

        slot_data.append(
            {
                'value':
                    slot.strftime('%H:%M'),

                'label':
                    slot.strftime('%I:%M %p')
            }
        )


    return JsonResponse(
        {
            'slots': slot_data
        }
    )
@login_required
@doctor_required
def doctor_appointment_detail(
    request,
    appointment_id
):

    doctor = get_object_or_404(
        Doctor,
        user=request.user
    )


    appointment = get_object_or_404(
        Appointment.objects.select_related(
            'patient',
            'department',
            'doctor'
        ),
        id=appointment_id,
        doctor=doctor
    )


    return render(
        request,
        'doctor/appointment_detail.html',
        {
            'doctor': doctor,
            'appointment': appointment,
        }
    )
@login_required
@admin_required
def hospital_admin_dashboard(request):

    today = timezone.localdate()


    # -----------------------------------
    # MAIN STATISTICS
    # -----------------------------------

    total_patients = Patient.objects.count()

    total_doctors = Doctor.objects.count()

    total_departments = Department.objects.count()


    today_appointments = Appointment.objects.filter(
        date=today
    )
    confirmed_today = today_appointments.filter(
        status='confirmed'
    ).count()


    completed_today = today_appointments.filter(
        status='completed'
    ).count()


    pending_appointments = Appointment.objects.filter(
        status='pending'
    )


    # -----------------------------------
    # RECENT APPOINTMENTS
    # -----------------------------------

    recent_appointments = (
        Appointment.objects.select_related(
            'patient',
            'doctor',
            'department'
        )
        .order_by(
            '-created_at'
        )[:8]
    )


    # -----------------------------------
    # DEPARTMENT STATISTICS
    # -----------------------------------

    department_stats = (
        Department.objects.annotate(
            doctor_count=Count(
                'doctor',
                distinct=True
            ),
            appointment_count=Count(
                'appointment',
                distinct=True
            )
        )
        .order_by(
            '-appointment_count'
        )
    )


    return render(
        request,
        'management/dashboard.html',
        {
            'today': today,

            'total_patients':
                total_patients,

            'total_doctors':
                total_doctors,

            'total_departments':
                total_departments,

            'today_appointments':
                today_appointments,

            'pending_appointments':
                pending_appointments,
            'confirmed_today': 
                confirmed_today,
            'completed_today': 
                completed_today,

            'recent_appointments':
                recent_appointments,

            'department_stats':
                department_stats,
        }
    )
@login_required
def notifications_list(request):

    notifications = (
        Notification.objects.filter(
            recipient=request.user
        )
        .select_related(
            'appointment',
            'appointment__doctor',
            'appointment__patient'
        )
    )


    return render(
        request,
        'notifications/list.html',
        {
            'notifications':
                notifications
        }
    )
@login_required
@require_POST
def open_notification(
    request,
    notification_id
):

    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user
    )


    if not notification.is_read:

        notification.is_read = True

        notification.save(
            update_fields=[
                'is_read'
            ]
        )


    appointment = (
        notification.appointment
    )


    if appointment:

        # Doctor opening notification
        if (
            appointment.doctor.user_id
            == request.user.id
        ):

            return redirect(
                'doctor_appointment_detail',
                appointment_id=appointment.id
            )


        # Patient opening notification
        if (
            appointment.patient.user_id
            == request.user.id
        ):

            return redirect(
                'appointment_detail',
                appointment_id=appointment.id
            )


    return login_redirect(request)
@login_required
@require_POST
def mark_all_notifications_read(
    request
):

    Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(
        is_read=True
    )


    messages.success(
        request,
        "All notifications marked as read."
    )


    return redirect(
        'notifications'
    )
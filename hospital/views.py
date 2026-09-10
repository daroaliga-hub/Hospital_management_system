from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .decorators import doctor_required, patient_required
from django.contrib.auth.models import Group
from .models import Department, Doctor, Patient, Appointment
from .forms import PatientRegistrationForm, AppointmentForm

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
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            patient_group = Group.objects.get(name="Patient")
            user.groups.add(patient_group)          
            Patient.objects.create(user=user, full_name=user.username)
            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect('dashboard')
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
            login(request, user)
            return redirect('dashboard')
        messages.error(request, "Invalid credentials")
    return render(
    request,
    'authentication/login.html'
)

@login_required
@patient_required
def dashboard(request):

    patient, created = Patient.objects.get_or_create(
        user=request.user,
        defaults={
            "full_name": request.user.username
        }
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
def update_appointment_status(request, appointment_id, status):

    appointment = get_object_or_404(
        Appointment,
        id=appointment_id
    )


    try:

        doctor = request.user.doctor

    except Doctor.DoesNotExist:

        messages.error(
            request,
            "Doctor account required."
        )

        return redirect('home')



    # Security check

    if appointment.doctor != doctor:

        messages.error(
            request,
            "You cannot modify this appointment."
        )

        return redirect(
            'doctor_dashboard'
        )



    if status in [
        'confirmed',
        'cancelled',
        'completed'
    ]:

        appointment.status = status

        appointment.save()


        messages.success(
            request,
            f"Appointment {status}."
        )



    return redirect(
        'doctor_dashboard'
    )
@login_required
def add_medical_notes(request, appointment_id):

    appointment = get_object_or_404(
        Appointment,
        id=appointment_id
    )


    if request.method == "POST":

        notes = request.POST.get(
            "medical_notes"
        )


        appointment.medical_notes = notes

        appointment.status = "completed"

        appointment.save()


        messages.success(
            request,
            "Medical notes saved."
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

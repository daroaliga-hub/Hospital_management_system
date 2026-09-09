from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
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

def register(request):
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
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
def dashboard(request):
    if hasattr(request.user, 'patient'):
        appointments = Appointment.objects.filter(patient=request.user.patient).order_by('-date')
    else:
        appointments = []
    return render(
    request,
    'patient/dashboard.html',
    {
        'appointments': appointments
    }
)

@login_required
def book_appointment(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = request.user.patient
            appointment.department = appointment.doctor.department
            appointment.save()
            messages.success(request, "Appointment booked successfully!")
            return redirect('dashboard')
    else:
        form = AppointmentForm()
    return render(request, 'book_appointment.html', {'form': form})

@login_required
def user_logout(request):
    logout(request)
    return redirect('home')


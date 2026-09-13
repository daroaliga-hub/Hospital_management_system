from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('doctors/', views.doctor_list, name='doctor_list'),
    path(
    'services/',
    views.services,
    name='services'
),

path(
    'departments/',
    views.departments,
    name='departments'
),

path(
    'locations/',
    views.locations,
    name='locations'
),

path(
    'about/',
    views.about,
    name='about'
),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('book-appointment/', views.book_appointment, name='book_appointment'),
    path( 'doctor/<int:id>/', views.doctor_profile, name='doctor_profile'),
    path( 'doctor-dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path( 'appointment/<int:appointment_id>/<str:status>/', views.update_appointment_status, name='update_appointment_status'),
    path( 'appointment/<int:appointment_id>/notes/', views.add_medical_notes, name='add_medical_notes'),
    path( 'management/doctors/create/', views.create_doctor, name='create_doctor'),
    path( 'profile/', views.patient_profile, name='patient_profile'),
    path( 'profile/edit/', views.edit_patient_profile, name='edit_patient_profile'),
    path( 'appointments/<int:appointment_id>/', views.appointment_detail, name='appointment_detail'),
    path( 'appointments/<int:appointment_id>/cancel/', views.cancel_patient_appointment, name='cancel_patient_appointment'),
    path(
    'doctor/schedule/',
    views.doctor_schedule,
    name='doctor_schedule'
),
    path(
    'doctor/schedule/',
    views.doctor_schedule,
    name='doctor_schedule'
),
    path(
    'api/appointment-slots/',
    views.appointment_slots,
    name='appointment_slots'
),
    path(
    'doctor/appointments/<int:appointment_id>/',
    views.doctor_appointment_detail,
    name='doctor_appointment_detail'
),
    path(
    'management/',
    views.hospital_admin_dashboard,
    name='hospital_admin_dashboard'
),
]

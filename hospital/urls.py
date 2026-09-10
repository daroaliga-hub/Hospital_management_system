from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('doctors/', views.doctor_list, name='doctor_list'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('book-appointment/', views.book_appointment, name='book_appointment'),
    path( 'doctor/<int:id>/', views.doctor_profile, name='doctor_profile'),
    path( 'doctor-dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path( 'appointment/<int:appointment_id>/<str:status>/', views.update_appointment_status, name='update_appointment_status'),
]

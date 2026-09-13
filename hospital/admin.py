from django.contrib import admin
from .models import Department, Doctor,DoctorAvailability, Patient, Appointment
from django.contrib.auth.models import Group

admin.site.register(Department)
@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'department',
        'experience',
        'rating',
    )

    search_fields = (
        'name',
        'department__name',
    )

    list_filter = (
        'department',
    )
@admin.register(DoctorAvailability)
class DoctorAvailabilityAdmin(admin.ModelAdmin):

    list_display = (
        'doctor',
        'weekday',
        'start_time',
        'end_time',
        'slot_duration',
    )

    list_filter = (
        'weekday',
        'doctor',
    )

    search_fields = (
        'doctor__name',
    )
admin.site.register(Patient)
admin.site.register(Appointment)

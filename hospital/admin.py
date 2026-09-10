from django.contrib import admin
from .models import Department, Doctor, Patient, Appointment
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
admin.site.register(Patient)
admin.site.register(Appointment)

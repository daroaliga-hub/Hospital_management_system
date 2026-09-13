from django.contrib import admin
from .models import Department, Doctor,DoctorAvailability, Patient, Appointment, Notification
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
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):

    list_display = (
        'recipient',
        'notification_type',
        'message',
        'is_read',
        'created_at',
    )

    list_filter = (
        'notification_type',
        'is_read',
        'created_at',
    )

    search_fields = (
        'recipient__username',
        'message',
    )
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q


# Create your models here.
class Department(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Doctor(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        #null=True, # For production, we would remove null=True.
        #blank=True
    )

    name = models.CharField(
        max_length=100
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE
    )

    qualification = models.CharField(
        max_length=200
    )

    experience = models.PositiveIntegerField()

    fee = models.DecimalField(
        max_digits=8,
        decimal_places=2
    )

    image = models.ImageField(
        upload_to='doctors/',
        blank=True,
        null=True
    )

    bio = models.TextField(
        blank=True
    )


    # New fields

    location = models.CharField(
        max_length=200,
        blank=True
    )

    languages = models.CharField(
        max_length=200,
        blank=True
    )



    rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        default=5.0
    )


    def __str__(self):

        return f"Dr. {self.name} ({self.department})"

class DoctorAvailability(models.Model):

    WEEKDAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='availability'
    )

    weekday = models.PositiveSmallIntegerField(
        choices=WEEKDAY_CHOICES
    )

    start_time = models.TimeField()

    end_time = models.TimeField()

    slot_duration = models.PositiveIntegerField(
        default=30,
        help_text='Appointment length in minutes'
    )

    class Meta:

        ordering = [
            'weekday',
            'start_time'
        ]

        constraints = [

            models.UniqueConstraint(
                fields=[
                    'doctor',
                    'weekday',
                    'start_time',
                    'end_time'
                ],
                name='unique_doctor_availability'
            )

        ]

    def __str__(self):

        return (
            f"{self.doctor.name} - "
            f"{self.get_weekday_display()} "
            f"{self.start_time} - {self.end_time}"
        )

class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,)
    full_name = models.CharField(max_length=150)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=[('Male','Male'),('Female','Female'),('Other','Other')])
    phone = models.CharField(max_length=15)
    address = models.TextField(blank=True)
    blood_group = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return self.full_name



class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    symptoms = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    medical_notes = models.TextField(blank=True)
    
    
    appointment_number = models.CharField(
    max_length=20,
    unique=True,
    blank=True
    )
    class Meta:

        constraints = [

            models.UniqueConstraint(
                fields=[
                    'doctor',
                    'date',
                    'time',
                ],
                condition=Q(
                    status__in=[
                        'pending',
                        'confirmed'
                    ]
                ),
                name='uniq_active_doctor_slot'
            ),

        models.UniqueConstraint(
            fields=[
                'patient',
                'date',
                'time',
            ],
            condition=Q(
                status__in=[
                    'pending',
                    'confirmed'
                ]
            ),
            name='uniq_active_patient_slot'
        ),
    ]


    indexes = [

        models.Index(
            fields=[
                'doctor',
                'date',
                'status'
            ]
        ),

        models.Index(
            fields=[
                'patient',
                'date',
                'status'
            ]
        ),
    ]

    
    def save(self, *args, **kwargs):

        if not self.appointment_number:
            
            self.appointment_number = (
                str(uuid.uuid4())[:8].upper()
            )

        super().save(*args, **kwargs)

    
    def __str__(self):
        return f"{self.patient} with Dr. {self.doctor} on {self.date}"

class Notification(models.Model):

    TYPE_CHOICES = [

        (
            'appointment_requested',
            'Appointment Requested'
        ),

        (
            'appointment_confirmed',
            'Appointment Confirmed'
        ),

        (
            'appointment_cancelled',
            'Appointment Cancelled'
        ),

        (
            'appointment_completed',
            'Appointment Completed'
        ),

        (
            'medical_notes_updated',
            'Medical Notes Updated'
        ),

        (
            'general',
            'General'
        ),
    ]


    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )


    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )


    notification_type = models.CharField(
        max_length=30,
        choices=TYPE_CHOICES,
        default='general'
    )


    message = models.CharField(
        max_length=255
    )


    is_read = models.BooleanField(
        default=False
    )


    created_at = models.DateTimeField(
        auto_now_add=True
    )


    class Meta:

        ordering = [
            '-created_at'
        ]


    def __str__(self):

        return (
            f"{self.recipient.username}: "
            f"{self.message}"
        )
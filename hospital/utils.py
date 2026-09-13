from datetime import datetime, timedelta
from django.utils import timezone
from .models import (Appointment, DoctorAvailability, Notification)


def doctor_is_available(
    doctor,
    appointment_date,
    appointment_time
):

    weekday = appointment_date.weekday()


    schedules = DoctorAvailability.objects.filter(
        doctor=doctor,
        weekday=weekday,
        start_time__lte=appointment_time,
        end_time__gt=appointment_time
    )


    for schedule in schedules:

        schedule_start = datetime.combine(
            appointment_date,
            schedule.start_time
        )

        requested_start = datetime.combine(
            appointment_date,
            appointment_time
        )


        minutes_from_start = int(
            (
                requested_start
                - schedule_start
            ).total_seconds()
            / 60
        )


        if (
            minutes_from_start
            % schedule.slot_duration
            != 0
        ):

            continue


        requested_end = (
            requested_start
            + timedelta(
                minutes=schedule.slot_duration
            )
        )


        schedule_end = datetime.combine(
            appointment_date,
            schedule.end_time
        )


        if requested_end <= schedule_end:

            return True


    return False

def get_available_time_slots(
    doctor,
    appointment_date
):

    # Do not generate slots for past dates.
    if appointment_date < timezone.localdate():

        return []


    weekday = appointment_date.weekday()


    schedules = DoctorAvailability.objects.filter(
        doctor=doctor,
        weekday=weekday
    ).order_by(
        'start_time'
    )


    # Pending and confirmed appointments
    # occupy a time slot.
    booked_times = set(

        Appointment.objects.filter(
            doctor=doctor,
            date=appointment_date,
            status__in=[
                'pending',
                'confirmed'
            ]
        ).values_list(
            'time',
            flat=True
        )

    )


    available_slots = []


    for schedule in schedules:

        current_slot = datetime.combine(
            appointment_date,
            schedule.start_time
        )


        schedule_end = datetime.combine(
            appointment_date,
            schedule.end_time
        )


        slot_length = timedelta(
            minutes=schedule.slot_duration
        )


        while (
            current_slot + slot_length
            <= schedule_end
        ):

            slot_time = (
                current_slot
                .time()
                .replace(
                    second=0,
                    microsecond=0
                )
            )


            # If booking for today,
            # hide times that have already passed.
            if (
                appointment_date
                == timezone.localdate()
            ):

                current_time = (
                    timezone.localtime()
                    .time()
                    .replace(
                        tzinfo=None,
                        second=0,
                        microsecond=0
                    )
                )


                if slot_time <= current_time:

                    current_slot += slot_length

                    continue


            if slot_time not in booked_times:

                available_slots.append(
                    slot_time
                )


            current_slot += slot_length


    # Remove duplicates and sort.
    available_slots = sorted(
        set(available_slots)
    )


    return available_slots

def create_notification(
    recipient,
    message,
    notification_type='general',
    appointment=None
):

    if recipient is None:

        return None


    return Notification.objects.create(
        recipient=recipient,
        message=message,
        notification_type=notification_type,
        appointment=appointment
    )
    
    
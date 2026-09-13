from datetime import datetime, timedelta

from .models import DoctorAvailability


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
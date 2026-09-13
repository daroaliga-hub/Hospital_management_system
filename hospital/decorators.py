from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def doctor_required(view_func):

    def wrapper(request, *args, **kwargs):

        if request.user.groups.filter(
            name="Doctor"
        ).exists():

            return view_func(
                request,
                *args,
                **kwargs
            )


        messages.error(
            request,
            "Doctor access required."
        )


        return redirect('home')


    return wrapper



def patient_required(view_func):

    def wrapper(request, *args, **kwargs):

        if request.user.groups.filter(
            name="Patient"
        ).exists():

            return view_func(
                request,
                *args,
                **kwargs
            )


        messages.error(
            request,
            "Patient access required."
        )


        return redirect('home')
    return wrapper


def admin_required(view_func):

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if (
            request.user.is_authenticated
            and (
                request.user.is_staff
                or request.user.is_superuser
            )
        ):

            return view_func(
                request,
                *args,
                **kwargs
            )

        messages.error(
            request,
            "Administrator access required."
        )

        return redirect('home')

    return wrapper
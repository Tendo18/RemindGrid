# tasks.py (in your users app)
from celery import shared_task
from .utils import (
    send_verification_email,
    send_login_email,
    send_password_reset_email,
    send_password_reset_confirmation_email,
    send_account_lock_email,
)


@shared_task
def send_verification_email_task(user_id, token):
    from .models import User
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return
    send_verification_email(user, token)


@shared_task
def send_password_reset_email_task(user_id, otp):
    from .models import User
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return
    send_password_reset_email(user, otp)


@shared_task
def send_password_reset_confirmation_email_task(user_id):
    from .models import User
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return
    send_password_reset_confirmation_email(user)


@shared_task
def send_account_lock_email_task(user_id):
    from .models import User
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return
    send_account_lock_email(user)
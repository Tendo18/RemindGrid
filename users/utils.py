import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
import random

logger = logging.getLogger(__name__)


def _send_templated_email(subject, template_name, context, to_email):
    html_content = render_to_string(template_name, context)
    text_content = strip_tags(html_content)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email],
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()


def send_verification_email(user, token):
    subject = 'Verify your RemindGrid email'
    verification_url = f'{settings.FRONTEND_URL}/verify-email/{token}'

    try:
        _send_templated_email(
            subject=subject,
            template_name='emails/verify_email.html',
            context={
                'user': user,
                'verification_url': verification_url,
                'frontend_url': settings.FRONTEND_URL,
            },
            to_email=user.email,
        )
        return True
    except Exception as e:
        logger.error(f"Error sending verification email to {user.email}: {e}")
        return False


def generate_authentication_token(user):
    token = RefreshToken.for_user(user)
    return {
        'refresh': str(token),
        'access': str(token.access_token),
    }


def send_login_email(user):
    subject = 'New login to your RemindGrid account'

    try:
        _send_templated_email(
            subject=subject,
            template_name='emails/login_notification.html',
            context={'user': user},
            to_email=user.email,
        )
        return True
    except Exception as e:
        logger.error(f"Error sending login notification email to {user.email}: {e}")
        return False


def generate_otp():
    return str(random.randint(100000, 999999))


def send_password_reset_email(user, otp):
    subject = 'Your RemindGrid password reset code'

    try:
        _send_templated_email(
            subject=subject,
            template_name='emails/password_reset.html',
            context={'user': user, 'otp': otp},
            to_email=user.email,
        )
        return True
    except Exception as e:
        logger.error(f"Error sending OTP email to {user.email}: {e}")
        return False


def send_password_reset_confirmation_email(user):
    subject = 'Your RemindGrid password was reset'

    try:
        _send_templated_email(
            subject=subject,
            template_name='emails/password_reset_confirmation.html',
            context={'user': user, 'frontend_url': settings.FRONTEND_URL},
            to_email=user.email,
        )
        return True
    except Exception as e:
        logger.error(f"Error sending password reset confirmation email to {user.email}: {e}")
        return False


def send_account_lock_email(user):
    subject = 'Your RemindGrid account has been temporarily locked'

    try:
        _send_templated_email(
            subject=subject,
            template_name='emails/account_locked.html',
            context={'user': user},
            to_email=user.email,
        )
        return True
    except Exception as e:
        logger.error(f"Error sending account locked email to {user.email}: {e}")
        return False
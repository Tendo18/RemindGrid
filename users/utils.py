from django.core.mail import send_mail
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
import random

#function to send verification email to user after registration with a unique token
def send_verification_email(user, token):
    subject = 'Email Verification'
    message = f'Please verify your email by clicking the following link: {settings.FRONTEND_URL}/verify-email/{token}'
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
    
 #function for generating token   
def generate_authentication_token(user):
    token = RefreshToken.for_user(user)
    return {
        'refresh': str(token),
        'access': str(token.access_token),
    }

#sending login notification email to user after successful login
def send_login_email(user):
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"EMAIL_HOST_PASSWORD: {settings.EMAIL_HOST_PASSWORD}")
    subject = 'Login Notification'
    message = f'''
    Hello {user.display_name},
    You have successfully logged in to your account.
    If this wasn't you, please contact support immediately.
    '''
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=False
        )
        return True
    except Exception as e:
        print(f"Error sending login notification email to {user.email}: {e}")
        return False
    
#function for generating OTP for password reset    
def generate_otp():
    return str(random.randint(100000, 999999))

#function for sending password reset email with OTP
def send_password_reset_email(user, otp):
    subject = 'Password Reset Request'
    message = f'''
    Hello {user.display_name},
    You requested a password reset. Use the code below to reset your password:
    {otp}
    
    This code will expire in 15 minutes. If you did not request a password reset, please ignore this email.
    
    '''
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=False
        )
        return True
    except Exception as e:
        print(f"Error sending OTP email to {user.email}: {e}")
        return False

#Confirmation email after password reset
def send_password_reset_confirmation_email(user):
    subject = 'Password Reset Successful'
    message = f'''
    Hello {user.display_name},
    Your password has been successfully reset. If you did not perform this action, please contact support immediately.
    
    '''
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=False
        )
        return True
    except Exception as e:
        print(f"Error sending password reset confirmation email to {user.email}: {e}")
        return False

#mail to notify user about lock
def send_account_lock_email(user):
    subject = 'Your account has been temporarily locked'
    message = f'''
    Hello {user.display_name},
    Your account was locked due to multiple failed login attempts.
    You can try logging in again after 15 minutes.
    If this wasn't you, we recommend resetting your password once your account unlocks.
    '''
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=False
        )
        return True
    except Exception as e:
        print(f"Error sending account locked email to {user.email}: {e}")
        return False    
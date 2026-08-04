from .models import User, PasswordResetOTP, EmailVerificationToken
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
import secrets
from .utils import generate_authentication_token, send_password_reset_confirmation_email, send_verification_email, send_login_email, generate_otp, send_password_reset_email, send_account_lock_email

EMAIL_EXPIRY_OTP_TIME = 15  # OTP expiry time

#service function to handle user registration, login, password reset, and email verification.
def create_email_verification_token(user):
    EmailVerificationToken.objects.filter(user=user, is_used=False).update(is_used=True)  # Update any used token to true
    token = secrets.token_urlsafe(32)
    EmailVerificationToken.objects.create(user=user, token=str(token), expires_at=timezone.now() + timedelta(minutes=EMAIL_EXPIRY_OTP_TIME))
    try:
        send_verification_email(user, token)
    except Exception as e:
        print(f"Error sending email: {e}")
    return str(token)

def register_user(validated_data):
    user = User.objects.create_user(**validated_data)
    token = create_email_verification_token(user)
    return user

def verify_email(email,token):
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        raise serializers.ValidationError("User with this email does not exist.")
    
    if user.is_verified:
        raise serializers.ValidationError("Email is already verified.")
    
    record = EmailVerificationToken.objects.filter(user=user, token=token, is_used=False).first()
    
    if not record or not record.is_valid():
        raise serializers.ValidationError("Invalid or expired token.")
    
    user.is_verified = True
    user.save()
    
    record.is_used = True
    record.save()
    
def resend_verification_email(user):
    if user.is_verified:
        raise serializers.ValidationError("Email is already verified.")
    token = create_email_verification_token(user)
    return token

def login_user(user):
    tokens = generate_authentication_token(user)
    try:
        send_login_email(user)
    except Exception as e:
        print(f"Error sending login notification email to {user.email}: {e}")
        
#service function to handle password reset request and sending OTP to user's email
OTP_EXPIRY_TIME = 15  # OTP expiry time in minutes
def create_password_reset_otp(user):
    PasswordResetOTP.objects.filter(user=user, is_used=False).update(is_used=True)  # Update any used OTP to true
    otp = generate_otp()
    PasswordResetOTP.objects.create(user=user, otp=otp, expires_at=timezone.now() + timedelta(minutes=OTP_EXPIRY_TIME))
    try:
        send_password_reset_email(user, otp)
    except Exception as e:
        print(f"Error sending password reset email: {e}")
    return otp

#service function to handle forgot password request and sending OTP to user's email
def request_forgot_password(user):
    create_password_reset_otp(user)

#service function to verify the OTP sent to user's email for password reset
def verify_password_reset_otp(email, otp):
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        raise serializers.ValidationError("Invalid email or OTP")
    
    record = PasswordResetOTP.objects.filter(user=user, otp=otp, is_used=False).first()
    
    if not record or not record.is_valid():
        raise serializers.ValidationError("Invalid or expired OTP")
    
    return user, record
    
#service function to handle password reset after verifying the OTP sent to user's email
def confirm_password_reset(user, otp_record, new_password):
    user.set_password(new_password)
    user.save()
    otp_record.is_used = True
    otp_record.save()
    try:
        send_password_reset_confirmation_email(user)
    except Exception as e:
        print(f"Error sending password reset confirmation email: {e}")
    return user

#service function to handle failed login attempt anad lockout user account after 5 failed attempts and send email notification to user
FAILED_LOGIN_ATTEMPTS_LIMIT = 3
LOCKOUT_TIME = 60 * 15  # Lockout time in minutes

#function to generate a unique cache key
def generate_lockout_key(email):
    return f"failed_login_attempts_{email}"

#function to check if a user is locked out based on their email
def is_user_locked_out(email):
    key = generate_lockout_key(email)
    failed_attempts = cache.get(key, 0)
    return failed_attempts >= FAILED_LOGIN_ATTEMPTS_LIMIT

#function to register a failed login attempt for a user based on their email
def register_failed_login_attempt(email):
    key = generate_lockout_key(email)
    failed_attempts = cache.get(key, 0)
    failed_attempts += 1
    cache.set(key, failed_attempts, LOCKOUT_TIME)
    
    try:
        user = User.objects.get(email=email)
        if failed_attempts >= FAILED_LOGIN_ATTEMPTS_LIMIT:
            try:
                send_account_lock_email(user)
            except Exception as e:
                print(f"Error sending account lock email to {user.email}: {e}")
    except User.DoesNotExist:
        pass  # If user doesn't exist, we don't need to send an email

#function to reset the failed login attempts for a user based on their email
def reset_failed_login_attempts(email):
    key = generate_lockout_key(email)
    cache.delete(key)
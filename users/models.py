from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager  

#Using a custom user model to use email as the unique identifier instead of username. 
# This is done by extending the AbstractUser class and overriding the USERNAME_FIELD attribute to 'email'. 
# The UserManager class is also customized to handle user creation with email and password.
# Create your models here.
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)
    
CURRENCY_CHOICES = (
    ('NGN', 'Nigerian Naira (₦)'),
    ('USD', 'US Dollar($)'),
    ('EUR', 'Euro(£)'),
    ('GBP', 'British Pound(€)')
)

class User(AbstractUser):
    username = None
    display_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(unique=True)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    is_verified =  models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Email & Password are required by default.
    
    
    objects = UserManager()
    
    def __str__(self):
        return self.email
 
class EmailVerificationToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=255, unique=True)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at
    
    def __str__(self):
        return f"Token for {self.user.email} - Expires at {self.expires_at}"
    
class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at
    
    def __str__(self):
        return f"OTP for {self.user.email} - Expires at {self.expires_at}"
    

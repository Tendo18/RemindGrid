from django.urls import path
from .views import (
    RegisterView, VerifyEmailView, ResendVerificationEmailView,
    LoginView, ForgotPasswordView, ResetPasswordView, UserDetailView, LogoutView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('resend-verification/', ResendVerificationEmailView.as_view(), name='resend-verification'),
    path('login/', LoginView.as_view(), name='login'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('profile/', UserDetailView.as_view(), name='user-detail'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
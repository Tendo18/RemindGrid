from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .serializers import (
    RegisterSerializer, UserSerializer,
    LoginSerializer, VerifyEmailSerializer, ResendVerificationEmailSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer, LogoutSerializer,
)
from .service import (
    register_user, verify_email, resend_verification_email,
    request_forgot_password, verify_password_reset_otp, confirm_password_reset,
    is_user_locked_out, register_failed_login_attempt, reset_failed_login_attempts,
    login_user
)

User = get_user_model()


@method_decorator(ratelimit(key='ip', rate='5/h', method='POST', block=True), name='post')
class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=RegisterSerializer,
        responses={201: UserSerializer, 400: OpenApiResponse(description="Bad Request")}
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = register_user(serializer.validated_data)
        return Response({
            'message': 'Registration successful. Please check your email to verify your account.',
            'user': UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)


@method_decorator(ratelimit(key='ip', rate='10/h', method='POST', block=True), name='post')
class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=VerifyEmailSerializer,
        responses={200: OpenApiResponse(description="Email verified successfully"), 400: OpenApiResponse(description="Bad Request")}
    )
    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        verify_email(serializer.validated_data['email'], serializer.validated_data['token'])
        return Response({"message": "Email verified successfully. You can now login."}, status=status.HTTP_200_OK)


@method_decorator(ratelimit(key='ip', rate='5/h', method='POST', block=True), name='post')
class ResendVerificationEmailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=ResendVerificationEmailSerializer,
        responses={200: OpenApiResponse(description="If the account exists, a verification email was sent")}
    )
    def post(self, request):
        serializer = ResendVerificationEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            resend_verification_email(user)
        except User.DoesNotExist:
            pass  # don't reveal whether the account exists
        return Response(
            {"message": "If that account exists, a verification email has been sent."},
            status=status.HTTP_200_OK
        )


@method_decorator(ratelimit(key='ip', rate='10/h', method='POST', block=True), name='post')
class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(description="Login successful"),
            401: OpenApiResponse(description="Invalid credentials"),
            403: OpenApiResponse(description="Email not verified"),
            423: OpenApiResponse(description="Account locked"),
        }
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        if is_user_locked_out(email):
            return Response(
                {"error": "Account temporarily locked due to multiple failed attempts. Try again later."},
                status=status.HTTP_423_LOCKED
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            register_failed_login_attempt(email)
            return Response({"error": "Invalid email or password."}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.check_password(password):
            register_failed_login_attempt(email)
            return Response({"error": "Invalid email or password."}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_verified:
            return Response({"error": "Please verify your email before logging in."}, status=status.HTTP_403_FORBIDDEN)

        reset_failed_login_attempts(email)
        tokens = login_user(user)
        return Response({"user": UserSerializer(user).data, **tokens}, status=status.HTTP_200_OK)


@method_decorator(ratelimit(key='ip', rate='5/h', method='POST', block=True), name='post')
class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=ForgotPasswordSerializer,
        responses={200: OpenApiResponse(description="If the account exists, an OTP was sent")}
    )
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            request_forgot_password(user)
        except User.DoesNotExist:
            pass  # don't reveal whether the account exists
        return Response(
            {"message": "If an account with that email exists, an OTP has been sent for password reset."},
            status=status.HTTP_200_OK
        )


@method_decorator(ratelimit(key='ip', rate='5/h', method='POST', block=True), name='post')
class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=ResetPasswordSerializer,
        responses={200: OpenApiResponse(description="Password reset successful"), 400: OpenApiResponse(description="Bad Request")}
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user, record = verify_password_reset_otp(
            serializer.validated_data['email'], serializer.validated_data['otp']
        )
        confirm_password_reset(user, record, serializer.validated_data['new_password'])

        return Response(
            {"message": "Password reset successful. You can now log in with your new password."},
            status=status.HTTP_200_OK
        )


class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: UserSerializer})
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(request=UserSerializer, responses={200: UserSerializer, 400: OpenApiResponse(description="Bad Request")})
    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=LogoutSerializer,
        responses={200: OpenApiResponse(description="Logged out successfully"), 400: OpenApiResponse(description="Bad Request")}
    )
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            token = RefreshToken(serializer.validated_data['refresh'])
            token.blacklist()
        except TokenError:
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)
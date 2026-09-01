import pytest
from django.core import mail
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from ..models import EmailVerificationToken, PasswordResetOTP


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def registration_data():
    return {
        'email': 'newuser@example.com',
        'display_name': 'New User',
        'password': 'testpass123',
        'password2': 'testpass123',
    }


@pytest.mark.django_db
class TestRegisterView:

    def test_valid_registration_succeeds(self, api_client, registration_data):
        response = api_client.post('/api/register/', registration_data)
        assert response.status_code == 201

    def test_new_user_is_unverified(self, api_client, registration_data):
        api_client.post('/api/register/', registration_data)
        from django.contrib.auth import get_user_model
        user = get_user_model().objects.get(email=registration_data['email'])
        assert user.is_verified is False

    def test_password_mismatch_fails(self, api_client, registration_data):
        registration_data['password2'] = 'different123'
        response = api_client.post('/api/register/', registration_data)
        assert response.status_code == 400

    def test_duplicate_email_fails(self, api_client, registration_data):
        api_client.post('/api/register/', registration_data)
        response = api_client.post('/api/register/', registration_data)
        assert response.status_code == 400

    def test_short_password_fails(self, api_client, registration_data):
        registration_data['password'] = 'short'
        registration_data['password2'] = 'short'
        response = api_client.post('/api/register/', registration_data)
        assert response.status_code == 400

    def test_registration_sends_verification_email(self, api_client, registration_data):
        api_client.post('/api/register/', registration_data)
        assert len(mail.outbox) == 1


@pytest.mark.django_db
class TestVerifyEmailView:

    def test_valid_token_verifies_user(self, api_client, create_user):
        user = create_user()
        token_record = EmailVerificationToken.objects.create(
            user=user, token='validtoken',
            expires_at=timezone.now() + timedelta(minutes=15)
        )
        response = api_client.post('/api/verify-email/', {
            'email': user.email, 'token': token_record.token
        })
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.is_verified is True

    def test_wrong_token_fails(self, api_client, create_user):
        user = create_user()
        EmailVerificationToken.objects.create(
            user=user, token='validtoken',
            expires_at=timezone.now() + timedelta(minutes=15)
        )
        response = api_client.post('/api/verify-email/', {
            'email': user.email, 'token': 'wrongtoken'
        })
        assert response.status_code == 400

    def test_unknown_email_fails(self, api_client):
        response = api_client.post('/api/verify-email/', {
            'email': 'nobody@example.com', 'token': 'sometoken'
        })
        assert response.status_code == 400


@pytest.mark.django_db
class TestResendVerificationEmailView:

    def test_resend_for_unverified_user_returns_200(self, api_client, unverified_user):
        response = api_client.post('/api/resend-verification/', {'email': unverified_user.email})
        assert response.status_code == 200

    def test_resend_for_unknown_email_still_returns_200(self, api_client):
        # deliberately doesn't reveal whether the account exists
        response = api_client.post('/api/resend-verification/', {'email': 'nobody@example.com'})
        assert response.status_code == 200


@pytest.mark.django_db
class TestLoginView:

    def test_correct_credentials_succeed(self, api_client, verified_user):
        response = api_client.post('/api/login/', {
            'email': verified_user.email, 'password': 'testpass123'
        })
        assert response.status_code == 200
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_wrong_password_fails(self, api_client, verified_user):
        response = api_client.post('/api/login/', {
            'email': verified_user.email, 'password': 'wrongpass'
        })
        assert response.status_code == 401

    def test_unknown_email_fails(self, api_client):
        response = api_client.post('/api/login/', {
            'email': 'nobody@example.com', 'password': 'whatever'
        })
        assert response.status_code == 401

    def test_unverified_user_cannot_login(self, api_client, unverified_user):
        response = api_client.post('/api/login/', {
            'email': unverified_user.email, 'password': 'testpass123'
        })
        assert response.status_code == 403

    def test_three_failed_attempts_locks_account(self, api_client, verified_user):
        for _ in range(3):
            api_client.post('/api/login/', {
                'email': verified_user.email, 'password': 'wrongpass'
            })
        # even correct password should now fail
        response = api_client.post('/api/login/', {
            'email': verified_user.email, 'password': 'testpass123'
        })
        assert response.status_code == 423

    def test_successful_login_resets_failed_attempts(self, api_client, verified_user):
        api_client.post('/api/login/', {'email': verified_user.email, 'password': 'wrongpass'})
        api_client.post('/api/login/', {'email': verified_user.email, 'password': 'testpass123'})
        # should not be locked out - only one failed attempt was registered
        response = api_client.post('/api/login/', {
            'email': verified_user.email, 'password': 'testpass123'
        })
        assert response.status_code == 200


@pytest.mark.django_db
class TestForgotPasswordView:

    def test_request_creates_otp(self, api_client, verified_user):
        response = api_client.post('/api/forgot-password/', {'email': verified_user.email})
        assert response.status_code == 200
        assert PasswordResetOTP.objects.filter(user=verified_user, is_used=False).exists()

    def test_unknown_email_still_returns_200(self, api_client):
        response = api_client.post('/api/forgot-password/', {'email': 'nobody@example.com'})
        assert response.status_code == 200


@pytest.mark.django_db
class TestResetPasswordView:

    def test_correct_otp_resets_password(self, api_client, verified_user):
        otp_record = PasswordResetOTP.objects.create(
            user=verified_user, otp='123456',
            expires_at=timezone.now() + timedelta(minutes=15)
        )
        response = api_client.post('/api/reset-password/', {
            'email': verified_user.email,
            'otp': otp_record.otp,
            'new_password': 'newpass456',
        })
        assert response.status_code == 200
        verified_user.refresh_from_db()
        assert verified_user.check_password('newpass456') is True

    def test_wrong_otp_fails(self, api_client, verified_user):
        PasswordResetOTP.objects.create(
            user=verified_user, otp='123456',
            expires_at=timezone.now() + timedelta(minutes=15)
        )
        response = api_client.post('/api/reset-password/', {
            'email': verified_user.email,
            'otp': '000000',
            'new_password': 'newpass456',
        })
        assert response.status_code == 400

    def test_short_new_password_fails(self, api_client, verified_user):
        otp_record = PasswordResetOTP.objects.create(
            user=verified_user, otp='123456',
            expires_at=timezone.now() + timedelta(minutes=15)
        )
        response = api_client.post('/api/reset-password/', {
            'email': verified_user.email,
            'otp': otp_record.otp,
            'new_password': 'short',
        })
        assert response.status_code == 400

    def test_old_password_no_longer_works(self, api_client, verified_user):
        otp_record = PasswordResetOTP.objects.create(
            user=verified_user, otp='123456',
            expires_at=timezone.now() + timedelta(minutes=15)
        )
        api_client.post('/api/reset-password/', {
            'email': verified_user.email,
            'otp': otp_record.otp,
            'new_password': 'newpass456',
        })
        response = api_client.post('/api/login/', {
            'email': verified_user.email, 'password': 'testpass123'
        })
        assert response.status_code == 401
import pytest
from django.core import mail
from django.utils import timezone
from datetime import timedelta
from rest_framework import serializers
from ..models import EmailVerificationToken, PasswordResetOTP
from ..service import (
    register_user, verify_email, resend_verification_email,
    create_password_reset_otp, verify_password_reset_otp, confirm_password_reset,
    is_user_locked_out, register_failed_login_attempt, reset_failed_login_attempts,
    login_user, FAILED_LOGIN_ATTEMPTS_LIMIT,
)


@pytest.mark.django_db
class TestRegisterUser:

    def test_creates_user_and_verification_token(self):
        user = register_user({
            'email': 'newuser@example.com',
            'password': 'testpass123',
            'display_name': 'New User',
        })
        assert user.pk is not None
        assert EmailVerificationToken.objects.filter(user=user, is_used=False).exists()

    def test_sends_verification_email(self):
        register_user({
            'email': 'newuser@example.com',
            'password': 'testpass123',
            'display_name': 'New User',
        })
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ['newuser@example.com']


@pytest.mark.django_db
class TestVerifyEmail:

    def test_valid_token_verifies_user(self, create_user):
        user = create_user()
        token_record = EmailVerificationToken.objects.create(
            user=user, token='validtoken',
            expires_at=timezone.now() + timedelta(minutes=15)
        )
        verify_email(user.email, token_record.token)
        user.refresh_from_db()
        assert user.is_verified is True

    def test_marks_token_used(self, create_user):
        user = create_user()
        token_record = EmailVerificationToken.objects.create(
            user=user, token='validtoken',
            expires_at=timezone.now() + timedelta(minutes=15)
        )
        verify_email(user.email, token_record.token)
        token_record.refresh_from_db()
        assert token_record.is_used is True

    def test_wrong_token_raises(self, create_user):
        user = create_user()
        EmailVerificationToken.objects.create(
            user=user, token='validtoken',
            expires_at=timezone.now() + timedelta(minutes=15)
        )
        with pytest.raises(serializers.ValidationError):
            verify_email(user.email, 'wrongtoken')

    def test_expired_token_raises(self, create_user):
        user = create_user()
        token_record = EmailVerificationToken.objects.create(
            user=user, token='validtoken',
            expires_at=timezone.now() - timedelta(minutes=1)
        )
        with pytest.raises(serializers.ValidationError):
            verify_email(user.email, token_record.token)

    def test_already_verified_raises(self, verified_user):
        token_record = EmailVerificationToken.objects.create(
            user=verified_user, token='validtoken',
            expires_at=timezone.now() + timedelta(minutes=15)
        )
        with pytest.raises(serializers.ValidationError):
            verify_email(verified_user.email, token_record.token)

    def test_unknown_email_raises(self):
        with pytest.raises(serializers.ValidationError):
            verify_email('nobody@example.com', 'sometoken')


@pytest.mark.django_db
class TestResendVerificationEmail:

    def test_invalidates_old_token_and_creates_new(self, create_user):
        user = create_user()
        old_token = EmailVerificationToken.objects.create(
            user=user, token='oldtoken',
            expires_at=timezone.now() + timedelta(minutes=15)
        )
        resend_verification_email(user)
        old_token.refresh_from_db()
        assert old_token.is_used is True
        assert EmailVerificationToken.objects.filter(user=user, is_used=False).count() == 1

    def test_already_verified_raises(self, verified_user):
        with pytest.raises(serializers.ValidationError):
            resend_verification_email(verified_user)


@pytest.mark.django_db
class TestPasswordResetFlow:

    def test_create_otp_invalidates_old_ones(self, verified_user):
        old_otp = PasswordResetOTP.objects.create(
            user=verified_user, otp='111111',
            expires_at=timezone.now() + timedelta(minutes=15)
        )
        create_password_reset_otp(verified_user)
        old_otp.refresh_from_db()
        assert old_otp.is_used is True
        assert PasswordResetOTP.objects.filter(user=verified_user, is_used=False).count() == 1

    def test_verify_returns_user_and_record(self, verified_user):
        otp_record = PasswordResetOTP.objects.create(
            user=verified_user, otp='123456',
            expires_at=timezone.now() + timedelta(minutes=15)
        )
        user, record = verify_password_reset_otp(verified_user.email, '123456')
        assert user == verified_user
        assert record == otp_record

    def test_verify_wrong_otp_raises(self, verified_user):
        PasswordResetOTP.objects.create(
            user=verified_user, otp='123456',
            expires_at=timezone.now() + timedelta(minutes=15)
        )
        with pytest.raises(serializers.ValidationError):
            verify_password_reset_otp(verified_user.email, '000000')

    def test_verify_expired_otp_raises(self, verified_user):
        PasswordResetOTP.objects.create(
            user=verified_user, otp='123456',
            expires_at=timezone.now() - timedelta(minutes=1)
        )
        with pytest.raises(serializers.ValidationError):
            verify_password_reset_otp(verified_user.email, '123456')

    def test_confirm_changes_password(self, verified_user):
        otp_record = PasswordResetOTP.objects.create(
            user=verified_user, otp='123456',
            expires_at=timezone.now() + timedelta(minutes=15)
        )
        confirm_password_reset(verified_user, otp_record, 'newpass456')
        verified_user.refresh_from_db()
        assert verified_user.check_password('newpass456') is True

    def test_confirm_marks_otp_used(self, verified_user):
        otp_record = PasswordResetOTP.objects.create(
            user=verified_user, otp='123456',
            expires_at=timezone.now() + timedelta(minutes=15)
        )
        confirm_password_reset(verified_user, otp_record, 'newpass456')
        otp_record.refresh_from_db()
        assert otp_record.is_used is True


@pytest.mark.django_db
class TestLoginLockout:

    def test_not_locked_out_initially(self):
        assert is_user_locked_out('someone@example.com') is False

    def test_locked_out_after_limit_reached(self):
        email = 'someone@example.com'
        for _ in range(FAILED_LOGIN_ATTEMPTS_LIMIT):
            register_failed_login_attempt(email)
        assert is_user_locked_out(email) is True

    def test_not_locked_out_before_limit_reached(self):
        email = 'someone@example.com'
        for _ in range(FAILED_LOGIN_ATTEMPTS_LIMIT - 1):
            register_failed_login_attempt(email)
        assert is_user_locked_out(email) is False

    def test_reset_clears_lockout(self):
        email = 'someone@example.com'
        for _ in range(FAILED_LOGIN_ATTEMPTS_LIMIT):
            register_failed_login_attempt(email)
        reset_failed_login_attempts(email)
        assert is_user_locked_out(email) is False

    def test_lockout_sends_email(self, verified_user):
        for _ in range(FAILED_LOGIN_ATTEMPTS_LIMIT):
            register_failed_login_attempt(verified_user.email)
        assert len(mail.outbox) == 1


@pytest.mark.django_db
class TestLoginUser:

    def test_returns_access_and_refresh_tokens(self, verified_user):
        tokens = login_user(verified_user)
        assert 'access' in tokens
        assert 'refresh' in tokens
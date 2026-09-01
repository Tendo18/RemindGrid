import pytest
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from ..models import EmailVerificationToken, PasswordResetOTP

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:

    def test_create_user_success(self, create_user):
        user = create_user(email='someone@Example.com', password='testpass123')
        assert user.email == 'someone@example.com'  # normalized to lowercase domain
        assert user.password != 'testpass123'  # hashed, not stored plain
        assert user.check_password('testpass123') is True
        assert user.is_verified is False
        assert user.is_active is True

    def test_create_user_without_email_raises(self):
        with pytest.raises(ValueError):
            User.objects.create_user(email='', password='testpass123')

    def test_create_superuser_sets_flags(self):
        admin = User.objects.create_superuser(email='admin@example.com', password='adminpass123')
        assert admin.is_staff is True
        assert admin.is_superuser is True

    def test_display_name_optional(self, create_user):
        user = create_user(display_name='')
        assert user.display_name == ''

    def test_str_returns_email(self, create_user):
        user = create_user(email='someone@example.com')
        assert str(user) == 'someone@example.com'


@pytest.mark.django_db
class TestEmailVerificationToken:

    def test_is_valid_when_fresh(self, create_user):
        token = EmailVerificationToken.objects.create(
            user=create_user(),
            token='sometoken',
            expires_at=timezone.now() + timedelta(minutes=15)
        )
        assert token.is_valid() is True

    def test_is_valid_false_when_expired(self, create_user):
        token = EmailVerificationToken.objects.create(
            user=create_user(),
            token='sometoken',
            expires_at=timezone.now() - timedelta(minutes=1)
        )
        assert token.is_valid() is False

    def test_is_valid_false_when_used(self, create_user):
        token = EmailVerificationToken.objects.create(
            user=create_user(),
            token='sometoken',
            expires_at=timezone.now() + timedelta(minutes=15),
            is_used=True
        )
        assert token.is_valid() is False


@pytest.mark.django_db
class TestPasswordResetOTP:

    def test_is_valid_when_fresh(self, create_user):
        otp = PasswordResetOTP.objects.create(
            user=create_user(),
            otp='123456',
            expires_at=timezone.now() + timedelta(minutes=15)
        )
        assert otp.is_valid() is True

    def test_is_valid_false_when_expired(self, create_user):
        otp = PasswordResetOTP.objects.create(
            user=create_user(),
            otp='123456',
            expires_at=timezone.now() - timedelta(minutes=1)
        )
        assert otp.is_valid() is False

    def test_is_valid_false_when_used(self, create_user):
        otp = PasswordResetOTP.objects.create(
            user=create_user(),
            otp='123456',
            expires_at=timezone.now() + timedelta(minutes=15),
            is_used=True
        )
        assert otp.is_valid() is False
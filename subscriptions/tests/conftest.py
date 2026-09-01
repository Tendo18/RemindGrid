import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from ..models import Subscription

User = get_user_model()


@pytest.fixture
def create_user(db):
    def _create_user(email='test@example.com', password='testpass123', display_name='Tester', is_verified=True):
        return User.objects.create_user(
            email=email,
            password=password,
            display_name=display_name,
            is_verified=is_verified,
        )
    return _create_user


@pytest.fixture
def user(create_user):
    return create_user()


@pytest.fixture
def create_subscription(db):
    def _create_subscription(
        user,
        name='Netflix',
        cost=Decimal('4500.00'),
        billing_cycle='monthly',
        category='entertainment',
        next_renewal_date=None,
        is_active=True,
    ):
        return Subscription.objects.create(
            user=user,
            name=name,
            cost=cost,
            billing_cycle=billing_cycle,
            category=category,
            next_renewal_date=next_renewal_date or (date.today() + timedelta(days=10)),
            is_active=is_active,
        )
    return _create_subscription
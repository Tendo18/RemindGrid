import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.db import IntegrityError
from ..models import Subscription, MonthlySpendSnapshot


@pytest.mark.django_db
class TestSubscriptionModel:

    def test_create_subscription_success(self, user, create_subscription):
        sub = create_subscription(user=user, name='Spotify', cost=Decimal('1500.00'))
        assert sub.pk is not None
        assert sub.is_active is True
        assert str(sub) == f"{sub.name} - {user.email}"

    def test_negative_cost_rejected_by_full_clean(self, user):
        sub = Subscription(
            user=user, name='Bad Sub', cost=Decimal('-10.00'),
            billing_cycle='monthly', category='other',
            next_renewal_date=date.today() + timedelta(days=5)
        )
        with pytest.raises(Exception):
            sub.full_clean()

    def test_zero_cost_rejected_by_full_clean(self, user):
        sub = Subscription(
            user=user, name='Free Sub', cost=Decimal('0.00'),
            billing_cycle='monthly', category='other',
            next_renewal_date=date.today() + timedelta(days=5)
        )
        with pytest.raises(Exception):
            sub.full_clean()

    def test_negative_cost_rejected_at_database_level(self, user):
        # bypasses full_clean() entirely - only the CheckConstraint can catch this
        with pytest.raises(IntegrityError):
            Subscription.objects.create(
                user=user, name='Bad Sub', cost=Decimal('-10.00'),
                billing_cycle='monthly', category='other',
                next_renewal_date=date.today() + timedelta(days=5)
            )

    def test_default_billing_cycle_is_monthly(self, user):
        sub = Subscription.objects.create(
            user=user, name='Default Sub', cost=Decimal('1000.00'),
            category='other', next_renewal_date=date.today() + timedelta(days=5)
        )
        assert sub.billing_cycle == 'monthly'


@pytest.mark.django_db
class TestMonthlySpendSnapshot:

    def test_create_snapshot(self, user):
        snapshot = MonthlySpendSnapshot.objects.create(
            user=user, month=date.today().replace(day=1), total_spend=Decimal('12000.00')
        )
        assert snapshot.summary_email_sent is False

    def test_unique_constraint_per_user_per_month(self, user):
        month = date.today().replace(day=1)
        MonthlySpendSnapshot.objects.create(user=user, month=month, total_spend=Decimal('12000.00'))
        with pytest.raises(IntegrityError):
            MonthlySpendSnapshot.objects.create(user=user, month=month, total_spend=Decimal('5000.00'))
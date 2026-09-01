import pytest
from decimal import Decimal
from datetime import date, timedelta
from ..models import Subscription, MonthlySpendSnapshot
from ..service import (
    monthly_equivalent,
    get_dashboard_summary,
    advance_renewal_date,
    roll_forward_expired_subscriptions,
    get_subscriptions_due_for_reminder,
    get_or_create_current_month_snapshot,
    get_previous_month_snapshot,
    get_snapshots_pending_summary_email,
)


class TestMonthlyEquivalent:

    def test_monthly_stays_the_same(self):
        assert monthly_equivalent(Decimal('1000.00'), 'monthly') == Decimal('1000.00')

    def test_yearly_divided_by_twelve(self):
        result = monthly_equivalent(Decimal('12000.00'), 'yearly')
        assert result == Decimal('1000.00')

    def test_weekly_multiplied_by_4_33(self):
        result = monthly_equivalent(Decimal('100.00'), 'weekly')
        assert result == Decimal('100.00') * Decimal('4.33')


@pytest.mark.django_db
class TestGetDashboardSummary:

    def test_totals_only_include_active_subscriptions(self, user, create_subscription):
        create_subscription(user=user, cost=Decimal('1000.00'), billing_cycle='monthly', is_active=True)
        create_subscription(user=user, cost=Decimal('5000.00'), billing_cycle='monthly', is_active=False)

        summary = get_dashboard_summary(user)
        assert summary['total_monthly_spend'] == Decimal('1000.00')

    def test_yearly_spend_is_monthly_times_twelve(self, user, create_subscription):
        create_subscription(user=user, cost=Decimal('1000.00'), billing_cycle='monthly')
        summary = get_dashboard_summary(user)
        assert summary['total_yearly_spend'] == Decimal('12000.00')

    def test_spend_by_category_groups_correctly(self, user, create_subscription):
        create_subscription(user=user, name='Netflix', cost=Decimal('1000.00'), category='entertainment')
        create_subscription(user=user, name='Spotify', cost=Decimal('500.00'), category='entertainment')
        create_subscription(user=user, name='Gym', cost=Decimal('2000.00'), category='fitness')

        summary = get_dashboard_summary(user)
        assert summary['spend_by_category']['entertainment'] == Decimal('1500.00')
        assert summary['spend_by_category']['fitness'] == Decimal('2000.00')

    def test_upcoming_renewals_sorted_soonest_first(self, user, create_subscription):
        create_subscription(user=user, name='Later', next_renewal_date=date.today() + timedelta(days=20))
        create_subscription(user=user, name='Soonest', next_renewal_date=date.today() + timedelta(days=2))

        summary = get_dashboard_summary(user)
        renewals = list(summary['upcoming_renewals'])
        assert renewals[0].name == 'Soonest'

    def test_trend_is_none_with_no_previous_month(self, user, create_subscription):
        create_subscription(user=user, cost=Decimal('1000.00'))
        summary = get_dashboard_summary(user)
        assert summary['trend'] is None

    def test_trend_calculated_against_previous_month(self, user, create_subscription):
        last_month = (date.today().replace(day=1) - timedelta(days=1)).replace(day=1)
        MonthlySpendSnapshot.objects.create(user=user, month=last_month, total_spend=Decimal('1000.00'))

        create_subscription(user=user, cost=Decimal('1500.00'), billing_cycle='monthly')
        summary = get_dashboard_summary(user)
        assert summary['trend'] == Decimal('500.00')


@pytest.mark.django_db
class TestAdvanceRenewalDate:

    def test_monthly_advances_by_one_month(self, user, create_subscription):
        sub = create_subscription(
            user=user, billing_cycle='monthly',
            next_renewal_date=date.today() - timedelta(days=1)
        )
        original = sub.next_renewal_date
        advance_renewal_date(sub)
        assert sub.next_renewal_date > date.today()
        assert sub.next_renewal_date.day == original.day  # relativedelta preserves day-of-month

    def test_weekly_advances_by_one_week_at_a_time(self, user, create_subscription):
        sub = create_subscription(
            user=user, billing_cycle='weekly',
            next_renewal_date=date.today() - timedelta(days=3)
        )
        advance_renewal_date(sub)
        assert sub.next_renewal_date >= date.today()

    def test_loops_until_date_is_in_the_future(self, user, create_subscription):
        # stale for 3 months - a single advance shouldn't be enough
        sub = create_subscription(
            user=user, billing_cycle='monthly',
            next_renewal_date=date.today() - timedelta(days=95)
        )
        advance_renewal_date(sub)
        assert sub.next_renewal_date >= date.today()

    def test_persists_to_database(self, user, create_subscription):
        sub = create_subscription(
            user=user, billing_cycle='monthly',
            next_renewal_date=date.today() - timedelta(days=1)
        )
        advance_renewal_date(sub)
        sub.refresh_from_db()
        assert sub.next_renewal_date >= date.today()


@pytest.mark.django_db
class TestRollForwardExpiredSubscriptions:

    def test_rolls_forward_only_expired_active_subscriptions(self, user, create_subscription):
        expired = create_subscription(
            user=user, name='Expired', next_renewal_date=date.today() - timedelta(days=1)
        )
        upcoming = create_subscription(
            user=user, name='Upcoming', next_renewal_date=date.today() + timedelta(days=5)
        )
        cancelled_expired = create_subscription(
            user=user, name='Cancelled', is_active=False,
            next_renewal_date=date.today() - timedelta(days=1)
        )

        roll_forward_expired_subscriptions()

        expired.refresh_from_db()
        upcoming.refresh_from_db()
        cancelled_expired.refresh_from_db()

        assert expired.next_renewal_date >= date.today()
        assert upcoming.next_renewal_date == date.today() + timedelta(days=5)  # untouched
        assert cancelled_expired.next_renewal_date == date.today() - timedelta(days=1)  # untouched, inactive


@pytest.mark.django_db
class TestGetSubscriptionsDueForReminder:

    def test_includes_subscriptions_within_three_days(self, user, create_subscription):
        due_soon = create_subscription(user=user, name='Due Soon', next_renewal_date=date.today() + timedelta(days=2))
        results = get_subscriptions_due_for_reminder()
        assert due_soon in results

    def test_excludes_subscriptions_further_out(self, user, create_subscription):
        far_out = create_subscription(user=user, name='Far Out', next_renewal_date=date.today() + timedelta(days=10))
        results = get_subscriptions_due_for_reminder()
        assert far_out not in results

    def test_excludes_inactive_subscriptions(self, user, create_subscription):
        inactive = create_subscription(
            user=user, name='Inactive', is_active=False,
            next_renewal_date=date.today() + timedelta(days=1)
        )
        results = get_subscriptions_due_for_reminder()
        assert inactive not in results


@pytest.mark.django_db
class TestSnapshots:

    def test_creates_snapshot_if_none_exists(self, user):
        snapshot = get_or_create_current_month_snapshot(user, Decimal('1000.00'))
        assert snapshot.total_spend == Decimal('1000.00')
        assert snapshot.month == date.today().replace(day=1)

    def test_updates_existing_current_month_snapshot(self, user):
        get_or_create_current_month_snapshot(user, Decimal('1000.00'))
        updated = get_or_create_current_month_snapshot(user, Decimal('1500.00'))
        assert updated.total_spend == Decimal('1500.00')
        assert MonthlySpendSnapshot.objects.filter(user=user).count() == 1

    def test_get_previous_month_snapshot(self, user):
        last_month = (date.today().replace(day=1) - timedelta(days=1)).replace(day=1)
        MonthlySpendSnapshot.objects.create(user=user, month=last_month, total_spend=Decimal('800.00'))

        result = get_previous_month_snapshot(user, date.today().replace(day=1))
        assert result.total_spend == Decimal('800.00')

    def test_get_snapshots_pending_summary_email(self, user):
        month = date.today().replace(day=1)
        pending = MonthlySpendSnapshot.objects.create(user=user, month=month, total_spend=Decimal('1000.00'))
        already_sent = MonthlySpendSnapshot.objects.create(
            user=user, month=month - timedelta(days=32), total_spend=Decimal('900.00'), summary_email_sent=True
        )

        results = get_snapshots_pending_summary_email(month)
        assert pending in results
        assert already_sent not in results
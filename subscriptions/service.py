from decimal import Decimal
from datetime import date, timedelta
from django.db.models import Sum, Case, When, F, DecimalField
from .models import Subscription, MonthlySpendSnapshot
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.template.loader import render_to_string

 
#converts any billing cycle into monthly cost
def monthly_equivalent(cost, billing_cycle):
    if billing_cycle == 'weekly':
        return cost * Decimal('4.33') #average number of weeks per month
    elif billing_cycle == 'yearly':
        return cost / Decimal('12')
    return cost

def get_dashboard_summary(user):
    subscriptions =  Subscription.objects.filter(user=user, is_active=True)
    total_monthly_spend = sum(
        (monthly_equivalent(sub.cost, sub.billing_cycle) for sub in subscriptions), Decimal('0.00')
    )
    total_yearly_spend = total_monthly_spend * 12
    upcoming_renewals = subscriptions.order_by('next_renewal_date')[:5]
    
    spend_by_category = {}
    for sub in subscriptions:
        monthly_cost = monthly_equivalent(sub.cost, sub.billing_cycle)
        spend_by_category[sub.category] = spend_by_category.get(sub.category, Decimal('0.00')) + monthly_cost
    
    current_month = date.today().replace(day=1)
    current_snapshot = get_or_create_current_month_snapshot(user, total_monthly_spend, category_breakdown={k: str(v) for k, v in spend_by_category.items()})
    previous_snapshot = get_previous_month_snapshot(user, current_month)
    
    trend = None
    if previous_snapshot:
        trend = round(total_monthly_spend - previous_snapshot.total_spend, 2)
        
    return {
        'trend': trend,
        'total_monthly_spend': round(total_monthly_spend, 2),
        'total_yearly_spend': round(total_yearly_spend, 2),
        'upcoming_renewals': upcoming_renewals,
        'spend_by_category': spend_by_category,
    }
    
def get_or_create_current_month_snapshot(user, current_total_monthly_spend, category_breakdown=None):
    current_month = date.today().replace(day=1)
    snapshot, created = MonthlySpendSnapshot.objects.get_or_create(
        user=user,
        month=current_month,
        defaults={
                'total_spend': current_total_monthly_spend,
                  'category_breakdown': category_breakdown or {}, 
                  }
    )
    if not created:
        # keep this month's snapshot up to date as subscriptions change during the month
        snapshot.total_spend = current_total_monthly_spend
        snapshot.category_breakdown = category_breakdown or {}
        snapshot.save()
    return snapshot


def get_previous_month_snapshot(user, current_month):
    return MonthlySpendSnapshot.objects.filter(
        user=user, month__lt=current_month
    ).order_by('-month').first()


def advance_renewal_date(subscription):
    today = timezone.now().date()
    while subscription.next_renewal_date < today:
        if subscription.billing_cycle == 'weekly':
            subscription.next_renewal_date += timedelta(weeks=1)
        elif subscription.billing_cycle == 'monthly':
            subscription.next_renewal_date += relativedelta(months=1)
        elif subscription.billing_cycle == 'yearly':
            subscription.next_renewal_date += relativedelta(years=1)
    subscription.save()


def roll_forward_expired_subscriptions():
    today = timezone.now().date()
    expired = Subscription.objects.filter(is_active=True, next_renewal_date__lt=today)
    for subscription in expired:
        advance_renewal_date(subscription)


def get_subscriptions_due_for_reminder():
    today = timezone.now().date()
    reminder_window_end = today + timedelta(days=3)
    return Subscription.objects.filter(
        is_active=True,
        next_renewal_date__gte=today,
        next_renewal_date__lte=reminder_window_end,
    )


def get_snapshots_pending_summary_email(month):
    return MonthlySpendSnapshot.objects.filter(month=month, summary_email_sent=False)
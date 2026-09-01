from celery import shared_task
from datetime import date, timedelta
from .utils import send_renewal_reminder_email, send_monthly_summary_email
from .service import (
    roll_forward_expired_subscriptions,
    get_subscriptions_due_for_reminder,
    get_snapshots_pending_summary_email,
    get_dashboard_summary,
)


@shared_task
def roll_forward_subscriptions_task():
    roll_forward_expired_subscriptions()


@shared_task
def send_renewal_reminders_task():
    from .models import Subscription
    subscriptions = get_subscriptions_due_for_reminder()
    for subscription in subscriptions:
        send_renewal_reminder_email(subscription)


@shared_task
def send_monthly_summary_emails_task():
    today = date.today()
    if today.day != 1:
        return

    last_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
    snapshots = get_snapshots_pending_summary_email(last_month)

    for snapshot in snapshots:
        summary = get_dashboard_summary(snapshot.user)
        send_monthly_summary_email(
            user=snapshot.user,
            snapshot=snapshot,
            trend=summary['trend'],
            spend_by_category=summary['spend_by_category'],
        )
        snapshot.summary_email_sent = True
        snapshot.save()


@shared_task
def daily_subscription_maintenance_task():
    """Runs once a day: rolls forward expired renewal dates, sends upcoming
    renewal reminders, and (only on the 1st) sends last month's summary emails."""
    roll_forward_subscriptions_task()
    send_renewal_reminders_task()
    send_monthly_summary_emails_task()
import logging
from decimal import Decimal
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from api.currency import format_money

logger = logging.getLogger(__name__)


def send_renewal_reminder_email(subscription):
    days_until_renewal = (subscription.next_renewal_date - subscription.next_renewal_date.today()).days
    user = subscription.user

    context = {
        'subscription': subscription,
        'user': user,
        'days_until_renewal': days_until_renewal,
        'formatted_cost': format_money(subscription.cost, user.currency),
        'manage_url': f"{settings.FRONTEND_URL}/subscriptions/{subscription.id}/",
    }

    subject = f"{subscription.name} renews in {days_until_renewal} day{'s' if days_until_renewal != 1 else ''}"
    text_content = (
        f"Hello {user.display_name or user.email},\n\n"
        f"Your {subscription.name} subscription renews on "
        f"{subscription.next_renewal_date.strftime('%B %d, %Y')} for {subscription.cost}."
    )
    html_content = render_to_string('emails/renewal_reminder.html', context)

    email = EmailMultiAlternatives(
        subject=subject, body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL, to=[user.email],
    )
    email.attach_alternative(html_content, "text/html")
    try:
        email.send()
        return True
    except Exception as e:
        logger.error(f"Error sending renewal reminder to {user.email}: {e}")
        return False


def send_monthly_summary_email(user, snapshot, trend, upcoming_renewals):
    total_spend = snapshot.total_spend
    trend_percent = None
    if trend is not None and snapshot.total_spend - trend != 0:
        previous_total = snapshot.total_spend - trend
        trend_percent = (trend / previous_total) * 100

    category_breakdown = [
        {'category': category.title(), 'amount': format_money(Decimal(amount), user.currency)}
        for category, amount in snapshot.category_breakdown.items()
    ]

    context = {
        'user': user,
        'month_label': snapshot.month.strftime('%B %Y'),
        'total_spend': total_spend,
        'trend_percent': trend_percent,
        'category_breakdown': category_breakdown,
        'upcoming_renewals': upcoming_renewals,
    }

    subject = f"Your RemindGrid summary for {context['month_label']}"
    text_content = f"Your total subscription spend for {context['month_label']} was {total_spend}."
    html_content = render_to_string('emails/monthly_summary.html', context)

    email = EmailMultiAlternatives(
        subject=subject, body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL, to=[user.email],
    )
    email.attach_alternative(html_content, "text/html")
    try:
        email.send()
        return True
    except Exception as e:
        logger.error(f"Error sending monthly summary to {user.email}: {e}")
        return False


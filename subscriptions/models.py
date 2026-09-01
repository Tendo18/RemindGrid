from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import CheckConstraint, Q
from django.core.validators import MinValueValidator
from decimal import Decimal


# Create your models here.
BILLING_CHOICES = (
    ('weekly', 'Weekly'),
    ('monthly', 'Monthly'),
    ('yearly', 'Yearly'),
)

CATEGORY_CHOICES = (
    ('entertainment', 'Entertainment'),
    ('education', 'Education'),
    ('productivity', 'Productivity'),
    ('health', 'Health'),
    ('finance', 'Finance'),
    ('social', 'Social'),
    ('shopping', 'Shopping'),
    ('news', 'News'),
    ('travel', 'Travel'),
    ('software', 'Software'),
    ('fitness', 'Fitness'),
    ('utilities', 'Utilities'),
    ('other', 'Other'),
)

class Subscription(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='subscriptions')
    name = models.CharField(max_length=100)
    cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    description = models.TextField(blank=True, null=True)
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CHOICES, default='monthly')
    next_renewal_date = models.DateField()  
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        constraints = [
            CheckConstraint(condition=Q(cost__gt=0), name='cost_positive'),
        ]   

    def __str__(self):
        return f"{self.name} - {self.user.email}"
    
class MonthlySpendSnapshot(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='spend_snapshots')
    month = models.DateField()
    total_spend = models.DecimalField(max_digits=10, decimal_places=2)
    category_breakdown = models.JSONField(default=dict)  # e.g., {"entertainment": 20.00, "education": 15.00}
    summary_email_sent = models.BooleanField(default=False)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'month'], name='unique_snapshot_per_user_per_month')
        ]
        
    def __str__(self):
        return f"{self.user.email} - {self.month.strftime('%B %Y')}: {self.total_spend}"
    

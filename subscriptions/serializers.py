from rest_framework import serializers
from .models import Subscription
from datetime import date
from api.currency import format_money     


class SubscriptionSerializer(serializers.ModelSerializer):
    days_until_renewal = serializers.SerializerMethodField()
    formatted_cost = serializers.SerializerMethodField()
    
    class Meta:
        model = Subscription
        fields = ['id', 'name', 'cost', 'formatted_cost', 'billing_cycle', 'category', 'next_renewal_date','days_until_renewal', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
        
    def get_days_until_renewal(self, obj):
        return (obj.next_renewal_date - date.today()).days
    
    def get_formatted_cost(self, obj):
        return format_money(obj.cost, obj.user.currency)
    
class DashboardSummarySerializer(serializers.Serializer):
    trend = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    total_monthly_spend = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_yearly_spend = serializers.DecimalField(max_digits=10, decimal_places=2)
    upcoming_renewals = SubscriptionSerializer(many=True)
    spend_by_category = serializers.DictField(child=serializers.DecimalField(max_digits=10, decimal_places=2))

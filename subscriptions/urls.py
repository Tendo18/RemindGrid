from django.urls import path
from .views import SubscriptionListCreateView, SubscriptionDetailView, DashboardView

urlpatterns = [
    path('subscriptions/', SubscriptionListCreateView.as_view(), name='subscription-list-create'),
    path('subscriptions/<int:pk>/', SubscriptionDetailView.as_view(), name='subscription-detail'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
]
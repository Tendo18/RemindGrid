from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Subscription
from .serializers import SubscriptionSerializer, DashboardSummarySerializer
from .service import get_dashboard_summary


class SubscriptionListCreateView(generics.ListCreateAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user).order_by('next_renewal_date')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SubscriptionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # scoped to the requesting user only - prevents accessing someone else's subscription by ID
        return Subscription.objects.filter(user=self.request.user)


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        responses={200: DashboardSummarySerializer}
    )
    def get(self, request):
        summary = get_dashboard_summary(request.user)
        serializer = DashboardSummarySerializer(summary)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

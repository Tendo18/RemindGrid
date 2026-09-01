import pytest
from decimal import Decimal
from datetime import date, timedelta
from rest_framework.test import APIClient
from ..models import Subscription


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.mark.django_db
class TestSubscriptionListCreateView:

    def test_create_subscription_succeeds(self, auth_client):
        response = auth_client.post('/api/subscriptions/', {
            'name': 'Netflix',
            'cost': '4500.00',
            'billing_cycle': 'monthly',
            'category': 'entertainment',
            'next_renewal_date': str(date.today() + timedelta(days=30)),
        })
        assert response.status_code == 201
        assert response.data['name'] == 'Netflix'

    def test_created_subscription_is_scoped_to_requesting_user(self, auth_client, user):
        auth_client.post('/api/subscriptions/', {
            'name': 'Netflix', 'cost': '4500.00', 'billing_cycle': 'monthly',
            'category': 'entertainment', 'next_renewal_date': str(date.today() + timedelta(days=30)),
        })
        sub = Subscription.objects.get(name='Netflix')
        assert sub.user == user

    def test_negative_cost_rejected(self, auth_client):
        response = auth_client.post('/api/subscriptions/', {
            'name': 'Bad Sub', 'cost': '-10.00', 'billing_cycle': 'monthly',
            'category': 'other', 'next_renewal_date': str(date.today() + timedelta(days=30)),
        })
        assert response.status_code == 400

    def test_list_only_shows_own_subscriptions(self, auth_client, user, create_user, create_subscription):
        create_subscription(user=user, name='Mine')
        other_user = create_user(email='other@example.com')
        create_subscription(user=other_user, name='NotMine')

        response = auth_client.get('/api/subscriptions/')
        names = [s['name'] for s in response.data]
        assert 'Mine' in names
        assert 'NotMine' not in names

    def test_unauthenticated_request_fails(self, api_client):
        response = api_client.get('/api/subscriptions/')
        assert response.status_code == 401

    def test_response_includes_days_until_renewal(self, auth_client, user, create_subscription):
        create_subscription(user=user, next_renewal_date=date.today() + timedelta(days=5))
        response = auth_client.get('/api/subscriptions/')
        assert response.data[0]['days_until_renewal'] == 5


@pytest.mark.django_db
class TestSubscriptionDetailView:

    def test_retrieve_own_subscription(self, auth_client, user, create_subscription):
        sub = create_subscription(user=user)
        response = auth_client.get(f'/api/subscriptions/{sub.id}/')
        assert response.status_code == 200
        assert response.data['name'] == sub.name

    def test_cannot_retrieve_another_users_subscription(self, auth_client, create_user, create_subscription):
        other_user = create_user(email='other@example.com')
        other_sub = create_subscription(user=other_user)
        response = auth_client.get(f'/api/subscriptions/{other_sub.id}/')
        assert response.status_code == 404

    def test_update_own_subscription(self, auth_client, user, create_subscription):
        sub = create_subscription(user=user, cost=Decimal('1000.00'))
        response = auth_client.patch(f'/api/subscriptions/{sub.id}/', {'cost': '2000.00'})
        assert response.status_code == 200
        sub.refresh_from_db()
        assert sub.cost == Decimal('2000.00')

    def test_delete_own_subscription(self, auth_client, user, create_subscription):
        sub = create_subscription(user=user)
        response = auth_client.delete(f'/api/subscriptions/{sub.id}/')
        assert response.status_code == 204
        assert not Subscription.objects.filter(id=sub.id).exists()

    def test_cannot_delete_another_users_subscription(self, auth_client, create_user, create_subscription):
        other_user = create_user(email='other@example.com')
        other_sub = create_subscription(user=other_user)
        response = auth_client.delete(f'/api/subscriptions/{other_sub.id}/')
        assert response.status_code == 404
        assert Subscription.objects.filter(id=other_sub.id).exists()


@pytest.mark.django_db
class TestDashboardView:

    def test_returns_correct_shape(self, auth_client, user, create_subscription):
        create_subscription(user=user, cost=Decimal('1000.00'), category='entertainment')
        response = auth_client.get('/api/dashboard/')
        assert response.status_code == 200
        assert 'total_monthly_spend' in response.data
        assert 'total_yearly_spend' in response.data
        assert 'upcoming_renewals' in response.data
        assert 'spend_by_category' in response.data
        assert 'trend' in response.data

    def test_unauthenticated_request_fails(self, api_client):
        response = api_client.get('/api/dashboard/')
        assert response.status_code == 401

    def test_only_includes_requesting_users_data(self, auth_client, user, create_user, create_subscription):
        create_subscription(user=user, cost=Decimal('1000.00'))
        other_user = create_user(email='other@example.com')
        create_subscription(user=other_user, cost=Decimal('99999.00'))

        response = auth_client.get('/api/dashboard/')
        assert Decimal(str(response.data['total_monthly_spend'])) == Decimal('1000.00')
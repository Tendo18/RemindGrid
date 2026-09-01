import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache

User = get_user_model()


@pytest.fixture
def create_user(db):
    """Factory fixture - call with overrides as needed, e.g. create_user(is_verified=True)"""
    def _create_user(email='test@example.com', password='testpass123', display_name='Tester', is_verified=False):
        return User.objects.create_user(
            email=email,
            password=password,
            display_name=display_name,
            is_verified=is_verified,
        )
    return _create_user


@pytest.fixture
def verified_user(create_user):
    return create_user(is_verified=True)


@pytest.fixture
def unverified_user(create_user):
    return create_user(email='unverified@example.com', is_verified=False)



@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


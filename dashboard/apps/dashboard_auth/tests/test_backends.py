import pytest

from dashboard_auth.backends import ModelBackend
from dashboard_auth.models import DashboardUser


@pytest.mark.parametrize('username, password, succeed', [
    ('foo', 'password', True),
    ('foo@example.com', 'password', True),

    ('foo', 'wrong_password', False),
    ('foo@example.com', 'wrong_password', False),
    ('not_exists_user', 'password', False),
    ('not_exists_email@example.com', 'password', False),
])
@pytest.mark.django_db
def test_login(username, password, succeed):
    user = DashboardUser.objects.create_user(
        username='foo',
        email='foo@example.com',
        password='password'
    )
    backend = ModelBackend()
    result = backend.authenticate(username=username, password=password)
    if succeed:
        assert result == user
    else:
        assert result is None

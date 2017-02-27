from unittest.mock import patch

from django.contrib.auth.models import User
import pytest


@pytest.mark.django_db
@patch('dashboard_auth.models.send_mail')
def test_send_email_to_new_user(send_mail):
    # create user will trigger email sending
    user = User.objects.create_user(
        username='username',
        email='username@email',
        password='Password1'
    )
    assert send_mail.call_count == 1
    send_mail.reset_mock()

    # update user will not trigger an email
    user.username = 'username2'
    user.save()
    send_mail.assert_not_called()

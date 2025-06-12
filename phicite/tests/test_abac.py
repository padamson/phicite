from app.api.users import enforcer


def test_regular_user_permissions(mock_user):
    assert enforcer.enforce(mock_user, "/users/me/", "GET")
    assert enforcer.enforce(mock_user, "/users/me/highlights/", "GET")
    assert not enforcer.enforce(mock_user, "/users/admin/username/", "GET")

def test_admin_user_permissions(mock_admin_user):
    assert enforcer.enforce(mock_admin_user, "/users/admin/username/", "GET")
    assert enforcer.enforce(mock_admin_user, "/users/admin/username/", "DELETE")
    assert enforcer.enforce(mock_admin_user, "/users/admin/id/", "GET")
    assert enforcer.enforce(mock_admin_user, "/users/admin/id/", "DELETE")
    assert enforcer.enforce(mock_admin_user, "/users/admin/email/", "GET")
    assert enforcer.enforce(mock_admin_user, "/users/admin/email/", "DELETE")
    assert enforcer.enforce(mock_admin_user, "/users/me/", "GET")
    assert enforcer.enforce(mock_admin_user, "/users/me/highlights/", "GET")
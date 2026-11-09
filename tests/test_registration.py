import pytest

from app.models import Student


def register(client, **overrides):
    """Submit a valid registration with any requested field overrides."""
    fields = {
        "student_id": "s123",
        "full_name": "A Student",
        "email": "student@example.edu",
        "password": "securepass",
    }
    fields.update(overrides)
    return client.post("/register", data=fields)


def test_registration_creates_account_and_allows_login(client, app):
    response = register(client)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")
    with app.app_context():
        student = Student.query.one()
        assert student.student_id == "s123"
        assert student.full_name == "A Student"
        assert student.email == "student@example.edu"

    response = client.post(
        "/login", data={"student_id": "s123", "password": "securepass"}
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    assert b"Welcome, A Student" in client.get("/").data


@pytest.mark.parametrize(
    "field", ["student_id", "full_name", "email", "password"]
)
def test_registration_rejects_missing_required_field(client, app, field):
    response = register(client, **{field: ""})

    assert response.status_code == 400
    assert b"All fields are required." in response.data
    with app.app_context():
        assert Student.query.count() == 0


def test_registration_rejects_malformed_email(client, app):
    response = register(client, email="not-an-email")

    assert response.status_code == 400
    assert b"Enter a valid email address." in response.data
    with app.app_context():
        assert Student.query.count() == 0


def test_registration_rejects_short_password(client, app):
    response = register(client, password="short")

    assert response.status_code == 400
    assert b"Password must be at least 8 characters long." in response.data
    with app.app_context():
        assert Student.query.count() == 0


def test_registration_rejects_duplicate_student_id(client, app):
    register(client)
    response = register(client, email="another@example.edu")

    assert response.status_code == 400
    assert b"student ID or email already exists" in response.data
    with app.app_context():
        assert Student.query.count() == 1


def test_registration_rejects_duplicate_email(client, app):
    register(client)
    response = register(client, student_id="another")

    assert response.status_code == 400
    assert b"student ID or email already exists" in response.data
    with app.app_context():
        assert Student.query.count() == 1


def test_registration_stores_only_password_hash(client, app):
    register(client)

    with app.app_context():
        student = Student.query.one()
        assert student.password_hash != "securepass"
        assert student.check_password("securepass")


def test_login_rejects_wrong_password(client, app):
    register(client)
    response = client.post(
        "/login", data={"student_id": "s123", "password": "incorrect"}
    )

    assert response.status_code == 401
    assert b"Invalid student ID or password." in response.data

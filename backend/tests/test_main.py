import pytest
from fastapi import status
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/healthz")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}


def test_default():
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "planspiegel_contacts API is running"}


def test_register():
    """
    Tests user registration endpoint with a valid email and password
    """

    data = {
        "email": "test@gmail.com",
        "password": "test"
    }
    response = client.post("/auth/register", json=data)
    assert response.status_code == status.HTTP_201_CREATED, f"Expected status code 201 (CREATED), got {response.status_code}"

    if len(response.json()) > 0:
        registration_data = response.json()
        assert "access_token" in registration_data
        assert "token_type" in registration_data
    else:
        raise AssertionError("Unexpected response structure")


@pytest.mark.dependency(depends=["test_register"])
def test_double_register():
    """
    Tests user re-registration
    """
    data = {
        "email": "test@gmail.com",
        "password": "test"
    }
    response = client.post("/auth/register", json=data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST, f"Expected status code 400 (BAD_REQUEST), got {response.status_code}"


@pytest.mark.dependency(depends=["test_register"])
def test_login():
    """
    Tests user registration endpoint with a valid email and password.
    """
    data = {
        "email": "test@gmail.com",
        "password": "test"
    }
    response = client.post("/auth/login", json=data)
    assert response.status_code == status.HTTP_200_OK, f"Expected status code 200 (SUCCESS), got {response.status_code}"

    if len(response.json()) > 0:
        registration_data = response.json()
        assert "access_token" in registration_data
        assert "token_type" in registration_data
    else:
        raise AssertionError("Unexpected response structure")


@pytest.mark.dependency(depends=["test_login"])
def test_set_cookie_handler():
    """
    Tests user registration endpoint with a valid email and password.
    """
    user_data = {
        "email": "test@gmail.com",
        "password": "test"
    }
    response_login = client.post("/auth/login", json=user_data)
    registration_data = response_login.json()
    token_data = {"token": registration_data["access_token"]}
    response_set_cookie = client.post("/auth/google-set-cookie", json=token_data)
    assert response_set_cookie.status_code == status.HTTP_200_OK, f"Expected status code 200 (SUCCESS), got {response_set_cookie.status_code}"


def test_set_cookie_handler_failure():
    """
    Tests user registration endpoint with a valid email and password.
    """
    token_data = {"token": "fake_token"}
    response_set_cookie = client.post("/auth/google-set-cookie", json=token_data)
    assert response_set_cookie.status_code == status.HTTP_401_UNAUTHORIZED, f"Expected status code 401 (UNAUTHORIZED), got {response_set_cookie.status_code}"

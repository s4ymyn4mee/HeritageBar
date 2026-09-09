import os
import pytest
TEST_USER_EMAIL = os.getenv("TEST_USER_EMAIL")
TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD")


class TestLoginPositive:
    def test_successful_login_and_session_storaging(self, client, base_url, login_test_data):
        login_response = client.post(
            f"{base_url}/login",
            data=login_test_data,
            allow_redirects=False,
            timeout=3
        )

        assert login_response.status_code == 302
        assert login_response.headers.get("Location") == "/profile"
        assert "connect.sid" in client.cookies, "Кука не добавилась :("

        profile_response = client.get(
            f"{base_url}/profile", 
            allow_redirects=False, 
            timeout=3
        )

        assert profile_response.status_code == 200, "Сервер попытался нас перенаправить (кука не сработала)"

    @pytest.mark.parametrize(
            "email, password",
            [
                (f"   {TEST_USER_EMAIL}   ", TEST_USER_PASSWORD),
                (TEST_USER_EMAIL.upper(), TEST_USER_PASSWORD)
            ],
            ids=[
                "extra_spaces",
                "case_sensitivity"
            ]
    )
    def test_weird_valid_email(self, client, base_url, email, password):
        weird_email_test_data = {
            "email": email,
            "password": password
        }

        login_response = client.post(
            f"{base_url}/login",
            data=weird_email_test_data,
            allow_redirects=False,
            timeout=3
        )

        assert login_response.status_code == 302
        assert login_response.headers.get("Location") == "/profile"
        assert "connect.sid" in client.cookies, "Кука не добавилась :("

        profile_response = client.get(
            f"{base_url}/profile",
            allow_redirects=False,
            timeout=3
        )

        assert profile_response.status_code == 200


class TestLoginNegative:
    def test_unauthorized_user_cannot_access_profile(self, client, base_url):
        response = client.get(
            f"{base_url}/profile", 
            allow_redirects=False, 
            timeout=3
        )

        assert response.status_code == 302
        assert response.headers.get("Location") == '/login'

    def test_unregistered_email_cannot_login(self, client, base_url):
        unregistered_login_data = {
            "email": "heritagebar.help@gmail.com",
            "password": "whatever"
        }

        login_response = client.post(
            f"{base_url}/login",
            data=unregistered_login_data,
            allow_redirects=False,
            timeout=3
        )
        assert login_response.status_code == 302
        assert login_response.headers.get("Location") == "/login"

        # Проверим, что логин действительно неудачный: переход на /profile должен редиректить на /login
        profile_response = client.get(
            f"{base_url}/profile",
            allow_redirects=False,
            timeout=3
        )

        assert profile_response.status_code == 302
        assert profile_response.headers.get("Location") == "/login"

    def test_existing_email_but_wrong_password(self, client, base_url, login_test_data):
        wrong_login_data = {
            "email": login_test_data.get("email"),
            "password": "so_wrong_password"
        }

        login_response = client.post(
            f"{base_url}/login",
            data=wrong_login_data,
            allow_redirects=False,
            timeout=3
        )

        assert login_response.status_code == 302
        assert login_response.headers.get("Location") == "/login"

        # Проверим, что логин действительно неудачный: переход на /profile должен редиректить на /login
        profile_response = client.get(
            f"{base_url}/profile",
            allow_redirects=False,
            timeout=3
        )

        assert profile_response.status_code == 302
        assert profile_response.headers.get("Location") == "/login"

    def test_unverified_user_cannot_login(self, client, base_url, unverified_user):
        """
        Пользователь с is_verified = false не должен получать сессию, а
        сервер обязан вернуть редирект на /login и не пускать в /profile
        """
        login_response = client.post(
            f"{base_url}/login",
            data=unverified_user,
            allow_redirects=False,
            timeout=3,
        )

        assert login_response.status_code == 302
        assert login_response.headers.get("Location") == "/login"

        profile_response = client.get(
            f"{base_url}/profile", 
            allow_redirects=False, 
            timeout=3
        )

        assert profile_response.status_code == 302
        assert profile_response.headers.get("Location") == "/login"


class TestSessionLifecycle:
    def test_logout_invalidates_session(self, authenticated_client, base_url):
        logout_response = authenticated_client.get(
            f"{base_url}/logout",
            allow_redirects=False,
            timeout=3
        )

        assert logout_response.status_code == 302
        assert logout_response.headers.get("Location") == "/login"
        assert "connect.sid" not in authenticated_client.cookies, "Кука не стерлась"

        profile_response = authenticated_client.get(
            f"{base_url}/profile",
            allow_redirects=False,
            timeout=3
        )
        
        assert profile_response.status_code == 302
        assert profile_response.headers.get("Location") == "/login"

    def test_session_id_regenerates_on_login(self, client, base_url, login_test_data):
        """
        Проверка защиты от фиксации сессии (атаки):
        Идентификатор сессии ОБяЗАН меняться после успешной аутентификации
        """

        # делаем анонимный запрос, получаем определенный session id
        client.get(f"{base_url}/login", timeout=3)
        initial_sid = client.cookies.get("connect.sid")

        client.post(
            f"{base_url}/login",
            data=login_test_data,
            allow_redirects=False,
            timeout=3
        )
        authenticated_sid = client.cookies.get("connect.sid")

        assert initial_sid != authenticated_sid, "УЯЗВИМОСТЬ! сервер сохранил старый session id после входа!"


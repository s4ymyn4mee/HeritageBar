import os
import time
import pytest
import requests
TEST_USER_EMAIL = os.getenv("TEST_USER_EMAIL")
TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD")


class TestLoginPositive:
    def test_unauthorized_user_cannot_access_profile(self, client, base_url):
        """
        Проверка, что неавторизованный пользователь не имеет доступа к профилю
        """
        response = client.get(
            f"{base_url}/profile", 
            allow_redirects=False, 
            timeout=3
        )

        assert response.status_code == 302
        assert response.headers.get("Location") == '/login'

    def test_successful_login_and_session_storaging(self, client, base_url, login_test_data):
        """
        Проверка успешного сценария логина и сохранения sid в куках
        """

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
        "payload",
        [
            {"email": f"   {TEST_USER_EMAIL}   ", "password": TEST_USER_PASSWORD},
            {"email": TEST_USER_EMAIL.upper(), "password": TEST_USER_PASSWORD}
        ],
        ids=[
            "extra_spaces",
            "case_sensitivity"
        ]
    )
    def test_weird_valid_email(self, client, base_url, payload):
        """
        Проверка позитивных сценариев странного ввода имейла
        """

        login_response = client.post(
            f"{base_url}/login",
            data=payload,
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
    def test_unverified_user_cannot_login(self, client, base_url, unverified_user):
        """
        Проверка того, что пользователь с is_verified = false не должен получать
        сессию, а сервер обязан вернуть редирект на /login и не пускать в /profile
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

    @pytest.mark.parametrize(
        "payload",
        [
            {"email": TEST_USER_EMAIL, "password": "so_wrong_password"},
            {"email": "heritagebar.help@gmail.com", "password": "whatever"},
            {"email": "not_even_an_email", "password": TEST_USER_PASSWORD},
            {"email": "@nodomain.com", "password": TEST_USER_PASSWORD},
            {"email": TEST_USER_EMAIL, "password": ""},
            {"email": "", "password": TEST_USER_PASSWORD},
            {"email": "", "password": ""},
            {"email": TEST_USER_EMAIL},
            {"password": TEST_USER_PASSWORD},
            {"email": TEST_USER_EMAIL, "asd": TEST_USER_PASSWORD},
            {"asd": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD},
            {"email": TEST_USER_EMAIL, "password": {}},
            {"email": {}, "password": TEST_USER_PASSWORD},
            {},
            {"email": TEST_USER_EMAIL, "password": 1000*"w"},
            {"email": f"{'w' * 1000}@example.com", "password": "any"},
            {"email": True, "password": TEST_USER_PASSWORD},
            {"email": TEST_USER_EMAIL, "password": True},
            {"email": 123, "password": TEST_USER_PASSWORD},
            {"email": TEST_USER_EMAIL, "password": 123},
        ],
        ids=[
            "valid_email_but_wrong_password",
            "unregistered_email_with_any_password",
            "no_sobachka_symbol_in_email",
            "no_domain_name_in_email",
            "valid_email_but_empty_password",
            "valid_password_but_empty_email",
            "empty_email_with_empty_password",
            "only_email",
            "only_password",
            "email_and_wrong_second_field_name",
            "password_and_wrong_second_field_name",
            "valid_email_but_password_is_dict",
            "valid_password_but_email_is_dict",
            "empty_payload",
            "email_with_giant_password",
            "giant_email_with_any_password",
            "valid_email_but_password_is_bool",
            "valid_password_but_email_is_bool",
            "valid_email_but_password_is_int",
            "valid_password_but_email_is_int"
        ]
    )
    def test_wrong_or_incorrect_payload(self, client, base_url, payload):
        """
        Проверка логина на ввод неверных или некорректных данных
        """
        login_response = client.post(
            f"{base_url}/login",
            data=payload,
            allow_redirects=False,
            timeout=3
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

class TestAppSecurity:
    @pytest.mark.parametrize(
        "payload",
        [
            {"email": "' OR '1'='1", "password": "any"},
            {"email": "' OR '1'='1' --", "password": "any"},
            {"email": "' OR 1=1 --", "password": "any"},
            {"email": "admin' --", "password": "any"},
            {"email": "admin@example.com'/*", "password": "any"},
            {"email": '" or ""=""', "password": "any"},
            {"email": "' or ''='", "password": "any"},

            {"email": "'", "password": "password"},
            {"email": "''", "password": "password"},
            {"email": "\\", "password": "password"},
            {"email": '"', "password": "password"},
            {"email": "';", "password": "password"},
            {"email": "'--", "password": "password"},
            {"email": "') OR ('1'='1", "password": "password"},
            {"email": "test' OR 'a'='a", "password": "' OR 'b'='b"},
            {"email": 'admin@example.com";', "password": "password"},

            {"email": "test@example.com' || pg_sleep(3) --", "password": "pass"},
            {"email": "'; SELECT pg_sleep(3); --", "password": "pass"},
            {
                "email": "1' AND (SELECT 1 FROM (SELECT(PG_SLEEP(3)))a) AND '1'='1",
                "password": "pass",
            },
            {
                "email": "admin@example.com' AND (SELECT 1 FROM pg_sleep(3)) IS NULL --",
                "password": "pass",
            },

            {"email": "test@example.com'; DROP TABLE users; --", "password": "any"},
            {
                "email": "test@example.com'; UPDATE users SET is_verified = true WHERE email = 'test@example.com'; --",
                "password": "any",
            },
            {
                "email": "test@example.com'; CREATE TABLE sqli_test (id int); --",
                "password": "any",
            },

            {"email": '"><script>alert(1)</script>', "password": "password"},
            {"email": '" onfocus="alert(1)" autofocus="', "password": "password"},
            {
                "email": '" autofocus onfocus="alert(document.cookie)',
                "password": "password",
            },
            {"email": '"><img src=x onerror=alert(1)>', "password": "password"},
            {"email": '"><svg onload=alert(1)>', "password": "password"},
            {"email": "' onfocus='alert(1)' autofocus='", "password": "password"},
            {
                "email": '<script src="https://attacker.test/xss.js"></script>',
                "password": "password",
            },
            {"email": "javascript:alert(1)", "password": "password"},

            {"email": "test@example.com\x00extra_padding", "password": "password"},
        ],
        ids=[
            "sqli_tautology_single_quotes",
            "sqli_tautology_with_comment",
            "sqli_tautology_numbers",
            "sqli_comment_out_password",
            "sqli_multiline_comment",
            "sqli_double_quotes_tautology",
            "sqli_empty_quotes_tautology",

            "sqli_syntax_single_quote",
            "sqli_syntax_double_single",
            "sqli_syntax_backslash",
            "sqli_syntax_double_quote",
            "sqli_syntax_quote_semicolon",
            "sqli_syntax_quote_dash",
            "sqli_syntax_closing_bracket",
            "sqli_syntax_both_fields",
            "sqli_syntax_double_quote_semicolon",

            "sqli_time_concat_pg_sleep",
            "sqli_time_stacked_pg_sleep",
            "sqli_time_subselect_pg_sleep",
            "sqli_time_null_pg_sleep",

            "sqli_stacked_drop_table",
            "sqli_stacked_update_field",
            "sqli_stacked_create_table",

            "xss_closing_tag_script",
            "xss_autofocus_attribute",
            "xss_autofocus_steal_cookie",
            "xss_img_onerror",
            "xss_svg_onload",
            "xss_single_quote_event_handler",
            "xss_external_script_tag",
            "xss_javascript_protocol",

            "edge_case_null_byte_in_string",
        ]
    )
    def test_login_security(self, client, base_url, payload):
        """
        Проверка логина на безопасность (SQL injections, XSS-attacks)
        """

        login_response = client.post(
            f"{base_url}/login",
            data=payload,
            allow_redirects=False,
            timeout=3.5
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
    def test_anonymous_session_destroys_on_successful_login(self, client, base_url, login_test_data):
        """
        Проверка защиты от атаки Fixation Session:
        Идентификатор сессии ОБяЗАН меняться после успешной аутентификации, а
        старый sid обязательно удаляться
        """

        # делаем анонимный запрос, получаем определенный session id
        client.get(f"{base_url}/login", timeout=3)
        initial_sid = client.cookies.get("connect.sid")
        assert initial_sid is not None, "Сервер не выдал начальную cookie сессии"

        client.post(
            f"{base_url}/login",
            data=login_test_data,
            allow_redirects=False,
            timeout=3
        )
        authenticated_sid = client.cookies.get("connect.sid")
        assert initial_sid != authenticated_sid, (
            "Уязвимость: сервер сохранил старый sid после входа")

        attacker_client = requests.Session()
        attacker_client.cookies.set("connect.sid", initial_sid)

        profile_response = attacker_client.get(
            f"{base_url}/profile", 
            allow_redirects=False, 
            timeout=3
        )

        assert profile_response.status_code == 302
        assert profile_response.headers.get("Location") == "/login"
        attacker_client.close()

    def test_logout_destroys_session_on_server(self, client, base_url, authenticated_client):
        """
        Проверка того, что сессия удаляется на сервере (клиент может сохранить, 
        но может и удалить её). Поэтому старый sid не должен давать доступа 
        к профилю после логаута
        """

        stolen_sid = authenticated_client.cookies.get("connect.sid")
        authenticated_client.get(
            f"{base_url}/logout", 
            allow_redirects=False
        )

        client.cookies.set("connect.sid", stolen_sid)
        response = client.get(
            f"{base_url}/profile", 
            allow_redirects=False, 
            timeout=3
        )

        assert response.status_code == 302
        assert response.headers.get("Location") == "/login"

    def test_session_cookie_security_attrs(self, client, base_url, login_test_data):
        """
        Проверка HttpOnly (от XSS-атак), SameSite (от CSRF-атак), 
        Path (защита от потери сессии) и Secure (HTTPS если предусмотрено)
        """
        client.post(
            f"{base_url}/login",
            data=login_test_data,
            allow_redirects=False,
            timeout=3,
        )

        cookie = next((c for c in client.cookies if c.name == "connect.sid"), None)
        assert cookie is not None, "Кука connect.sid не найдена"    

        is_http_only = cookie.has_nonstandard_attr("HttpOnly") or \
            "HttpOnly" in getattr(cookie, "_rest", {})
        assert is_http_only, "Уязвимость: отсутствует флаг HttpOnly"

        same_site = (getattr(cookie, "_rest", {})
                     .get("SameSite", "").strip().capitalize())
        assert same_site in ["Lax", "Strict"], (
            "Небезопасный SameSite, ожидался Lax или Strict")

        assert cookie.path == "/", "Ожидался Path=/"

        if base_url.startswith("https://"):
            assert cookie.secure, "Уязвимость: по HTTPS нет флага Secure"

    @pytest.mark.parametrize(
        "corrupted_sid",
        [
            "s%3Ainvalid_gibberish.signature",  # невалидная HMAC-подпись
            "s%3Anot_a_uuid_at_all.badhash",  # мусорный payload
            "plain_text_without_signature",  # без префикса s:
            "s%3A.",  # сломанный разделитель
            "",
        ],
        ids=[
            "invalid_signature",
            "corrupted_payload",
            "unsigned_sid",
            "broken_format",
            "empty_sid",
        ],
    )   
    def test_bad_sid_doesnt_crash_server(self, client, base_url, corrupted_sid):
        """
        Проверка устойчивости сервака к поддельному или битому connect.sid
        """

        client.cookies.set("connect.sid", corrupted_sid)

        response = client.get(
            f"{base_url}/profile",
            allow_redirects=False,
            timeout=3,
        )

        assert response.status_code == 302
        assert response.headers.get("Location") == "/login"

    def test_session_cookie_has_valid_ttl(self, client, base_url, login_test_data):
        """
        Проверка, что сервер выставляет TTL (Expires или max-age),
        а не бессрочную или чисто сессионную куку.
        """

        client.post(
            f"{base_url}/login",
            data=login_test_data,
            allow_redirects=False,
            timeout=3,
        )

        cookie = next((c for c in client.cookies if c.name == "connect.sid"), None)
        assert cookie is not None, "Кука connect.sid не найдена"
        assert cookie.expires is not None, "У куки нету времени истечения"

        current_time = time.time()
        ttl_seconds = cookie.expires - current_time
        assert ttl_seconds > 0, (
            f"Кука пришла уже просроченной: {ttl_seconds} секунд")

        expected_ttl = 7 * 24 * 60 * 60  # это 7 дней
        network_tolerance = 10
        assert abs(ttl_seconds - expected_ttl) < network_tolerance, (
            f"Неожиданный TTL сессии: {ttl_seconds} сек")

    def test_expired_session_denies_access(self, client, authenticated_client, base_url, db_connection):
        """
        Проверка, что при отправке устаревшей сессии сервер отказывает в авторизации
        """

        valid_sid = authenticated_client.cookies.get("connect.sid")
        assert valid_sid is not None

        with db_connection.cursor() as db_cursor:
            db_cursor.execute("UPDATE session SET expire = NOW() - INTERVAL '1 hour'")

        client.cookies.set("connect.sid", valid_sid)

        profile_response = client.get(
            f"{base_url}/profile",
            allow_redirects=False,
            timeout=3,
        )

        assert profile_response.status_code == 302
        assert profile_response.headers.get("Location") == "/login"


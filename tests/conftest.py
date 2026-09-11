
from dotenv import load_dotenv
import os
import pytest
import requests
import uuid
import bcrypt
import psycopg2

# Получаем полный путь текущей директории, переходим на уровень выше и извлекаем .env
current_directory = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_directory, "..", ".env")
load_dotenv(dotenv_path=env_path)

@pytest.fixture(scope="session")
def base_url():
    """
    Фикстура для получения базового URL из .env
    """

    url = os.getenv("BASE_URL")
    if not url:
        raise ValueError("BASE_URL не найден в файле .env, добавьте его")

    return url

@pytest.fixture(scope="function")
def client():
    """
    Фикстура для создания чистой сессии на каждый тест
    """

    with requests.Session() as session:
        yield session

@pytest.fixture(scope="function")
def login_test_data():
    # это специальный тестовый аккаунт
    login_payload = {
        "email": os.getenv("TEST_USER_EMAIL"),
        "password": os.getenv("TEST_USER_PASSWORD")
    }

    return login_payload

@pytest.fixture(scope="function")
def authenticated_client(client, base_url, login_test_data):
    """
    Фикстура, которая берет чистый client, логинит его в тестовый
    аккаунт и отдает в тест с уже готовой авторизованной печенькой
    """
    login_response = client.post(
        f"{base_url}/login",
        data=login_test_data,
        allow_redirects=False,
        timeout=3
    )

    assert login_response.status_code == 302, "SETUP провален: не удалось авторизоваться"
    assert login_response.headers.get("Location") == "/profile"
    assert "connect.sid" in client.cookies, "SETUP провален: нет куки сессии"
    
    return client

@pytest.fixture(scope="session")
def db_connection():
    """
    Открывает соединение с PostgreSQL на время выполнения всех тестов.
    """
    connection = psycopg2.connect(
        dbname=os.getenv("DATABASE"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
    connection.autocommit = True
    yield connection

    # teardown
    connection.close()

@pytest.fixture(scope="function")
def unverified_user(db_connection):
    """
    Создает пользователя с is_verified = FALSE напрямую в БД,
    после теста удаляет его. Использует БД напрямую, чтобы не получить
    бан почты, с которой рассылаются письма с подтверждениями
    """

    unique_suffix = uuid.uuid4().hex[:6]
    test_email = f"unverified_{unique_suffix}@heritage-bar.local"
    test_password = "Secret67"

    hashed_password = bcrypt.hashpw(
        test_password.encode("utf-8"), 
        bcrypt.gensalt(10)
    ).decode("utf-8")

    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO users (username, email, password, is_verified)
            VALUES (%s, %s, %s, FALSE)
            RETURNING user_id;
            """,
            (f"TestUnverifiedUser", test_email, hashed_password)
        )

    unverified_user_data = {
        "email": test_email,
        "password": test_password
    }

    yield unverified_user_data

    # teardown
    with db_connection.cursor() as cursor:
        cursor.execute("DELETE FROM users WHERE email = %s;", (test_email,))

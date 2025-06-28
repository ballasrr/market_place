"""
Модуль команд для управления инфраструктурой разработки.

Основной Flow:
1. dev() -> Главная команда разработки:
   - start_infrastructure() -> Запуск всей инфраструктуры
     - load_env_vars() -> Загрузка конфигурации
     - Проверка занятых портов через is_port_free()
     - Проверка Docker daemon
     - run_compose_command("down") -> Очистка старых контейнеров
     - get_available_port() -> Поиск свободных портов для сервисов
     - run_compose_command("up -d") -> Запуск контейнеров
     - check_services() -> Ожидание готовности сервисов
     - migrate() -> Применение миграций БД
   - find_free_port() -> Поиск порта для FastAPI
   - uvicorn.run() -> Запуск сервера разработки

Вспомогательные команды:
- serve() -> Только сервер без инфраструктуры
- start_all() -> migrate() + serve()
- setup()/activate() -> Настройка окружения через скрипты

Утилиты проверки:
- create_database() -> Создание БД если не существует
- get_postgres_container_name() -> Поиск контейнера PostgreSQL
"""
import asyncio
import os
import platform
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Optional

import asyncpg
import uvicorn

from app.core.dependencies import database_client, get_db_session
from app.core.security.password import pwd_context
from app.models import UserModel, UserRole


class DockerDaemonNotRunningError(Exception):
    """
    Исключение, возникающее когда Docker демон не запущен или недоступен.
    """

    def __init__(self, message=None):
        self.message = (
            message
            or "Docker демон не запущен. Убедись, что Docker Desktop запущен и работает."
        )
        super().__init__(self.message)


class DockerContainerConflictError(Exception):
    """
    Исключение, возникающее при конфликте имен контейнеров Docker.
    """

    def __init__(self, container_name=None, message=None):
        if container_name:
            self.message = (
                message
                or f"Конфликт имен контейнеров. Контейнер '{container_name}' уже используется. Удали его или переименуй."
            )
        else:
            self.message = (
                message
                or "Конфликт имен контейнеров. Удали существующий контейнер или переименуй его."
            )
        super().__init__(self.message)


TEST_ENV_FILE = ".env.test"
DEV_ENV_FILE = ".env.dev"
# Получаем путь к корню проекта
ROOT_DIR = Path(__file__).parents[1]

COMPOSE_FILE_WITHOUT_BACKEND = "docker-compose.dev.yml"

DEFAULT_PORTS = {
    "FASTAPI": 8000,
    "RABBITMQ": 5672,  # Порт для AMQP
    "RABBITMQ_UI": 15672,  # Порт для веб-интерфейса
    "POSTGRES": 5432,
    "REDIS": 6379,
    "PGADMIN": 5050,
    "REDIS_COMMANDER": 8081,
}


def load_env_vars(env_file_path: str = None) -> dict:
    """
    Загружает переменные окружения из .env файла
    Args:
        env_file_path: Путь к файлу .env. Если None, используется тестовый файл
    Returns:
        dict: Словарь с переменными окружения
    """
    if env_file_path is None:
        # Для тестов используем .env.test, если есть, иначе .env.dev
        dev_env_path = ROOT_DIR / DEV_ENV_FILE
        test_env_path = ROOT_DIR / TEST_ENV_FILE

        if dev_env_path.exists():
            env_file_path = str(dev_env_path)
            print(f"📋 Используем dev конфигурацию: {DEV_ENV_FILE}")
        elif test_env_path.exists():
            env_file_path = str(test_env_path)
            print(f"📋 Используем тестовую конфигурацию: {TEST_ENV_FILE}")
        else:
            print("❌ Не найден файл конфигурации (.env.dev или .env.test)")
            return {}

    env_vars = {}
    if os.path.exists(env_file_path):
        with open(env_file_path, encoding="utf-8") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    try:
                        key, value = line.strip().split("=", 1)
                        # Убираем кавычки если есть
                        value = value.strip("\"'")
                        env_vars[key] = value
                    except ValueError:
                        # Пропускаем некорректные строки
                        pass
    else:
        print(f"❌ Файл конфигурации не найден: {env_file_path}")

    return env_vars


def run_compose_command(
    command: str | list,
    compose_file: str = COMPOSE_FILE_WITHOUT_BACKEND,
    env: dict = None,
) -> None:
    """
    Запускает docker-compose команду в корне проекта

    Args:
        command: Команда для docker-compose
        compose_file: Путь к docker-compose файлу. По умолчанию используется COMPOSE_FILE_WITHOUT_BACKEND из констант
        env: Переменные окружения для docker-compose. По умолчанию используется DEV_ENV_FILE из констант

    Returns:
        None

    Raises:
        DockerDaemonNotRunningError: Если демон Docker не запущен
        DockerContainerConflictError: Если контейнер уже запущен
        FileNotFoundError: Если файл .env.dev или docker-compose файл не найден
    """
    if isinstance(command, str):
        command = command.split()

    # Проверяем наличие файла docker-compose
    compose_path = os.path.join(ROOT_DIR, compose_file)
    if not os.path.exists(compose_path):
        print(f"❌ Файл {compose_file} не найден в директории {ROOT_DIR}")
        raise FileNotFoundError(f"❌ Файл {compose_file} не найден в {ROOT_DIR}")

    # Проверяем наличие .env.dev
    env_path = os.path.join(ROOT_DIR, DEV_ENV_FILE)
    if not os.path.exists(env_path):
        print(f"❌ Файл {DEV_ENV_FILE} не найден в директории {ROOT_DIR}")
        print("💡 Создайте файл .env.dev с необходимыми переменными окружения")
        raise FileNotFoundError(
            f"❌ Файл {DEV_ENV_FILE} не найден. Создайте его перед запуском."
        )

    # Обновляем переменные окружения
    environment = os.environ.copy()
    # Добавляем переменные из DEV_ENV_FILE
    environment.update(load_env_vars())
    if env:
        environment.update(env)

    # show_output = any(cmd in command for cmd in ['up', 'build'])

    try:
        subprocess.run(
            ["docker-compose", "-f", compose_file] + command,
            cwd=ROOT_DIR,
            check=True,
            env=environment,
            # capture_output=not show_output,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        error_output = e.stderr or e.stdout or str(e)
        if (
            "docker daemon is not running" in error_output
            or "pipe/docker_engine" in error_output
        ):
            raise DockerDaemonNotRunningError() from e
        elif (
            "Conflict" in error_output
            and "is already in use by container" in error_output
        ):
            import re

            container_match = re.search(r'The container name "([^"]+)"', error_output)
            container_name = container_match.group(1) if container_match else None
            raise DockerContainerConflictError(container_name) from e
        raise


def find_free_port(start_port: int = 8000) -> int:
    """
    Ищет первый свободный порт начиная с указанного.

    Используется для FastAPI сервера в dev режиме.
    Проверяет возможность bind на порт через socket.

    Args:
        start_port: Начальный порт для поиска

    Returns:
        int: Номер свободного порта

    Raises:
        RuntimeError: Если все порты до 65535 заняты
    """
    port = start_port
    while port < 65535:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", port))
                return port
        except OSError:
            port += 1
    raise RuntimeError("Нет свободных портов! Ахуеть!")


def get_available_port(default_port: int) -> int:
    """
    Аналог find_free_port но с другим сообщением об ошибке.

    Дублирует логику find_free_port. Используется для поиска
    портов инфраструктурных сервисов в start_infrastructure.

    Args:
        default_port: Предпочитаемый порт

    Returns:
        int: Свободный порт

    Raises:
        RuntimeError: С указанием конкретного порта в ошибке
    """
    port = default_port
    while port < 65535:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", port))
                return port
        except OSError:
            port += 1
    raise RuntimeError(f"Не могу найти свободный порт после {default_port}")


def is_port_free(port: int) -> bool:
    """
    Проверяет доступность конкретного порта.

    Используется для валидации портов из .env.dev перед запуском
    инфраструктуры. Возвращает булево значение вместо исключения.

    Args:
        port: Номер порта для проверки

    Returns:
        bool: True если порт свободен, False если занят
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", port))
            return True
    except OSError:
        return False


def get_port(service: str) -> int:
    """
    Получает порт сервиса из переменных окружения или дефолтный.

    Преобразует имя сервиса в формат переменной окружения
    и ищет значение. Fallback на DEFAULT_PORTS.

    Args:
        service: Имя сервиса (например 'REDIS_PORT')

    Returns:
        int: Номер порта для сервиса

    Note:
        Убирает '_PORT' из имени и приводит к верхнему регистру
    """
    service_upper = service.upper().replace("_PORT", "")
    return int(os.getenv(service, DEFAULT_PORTS[service_upper]))


def show_loader(message: str, stop_event: threading.Event):
    """
    Показывает анимированный loader

    Args:
        message: Сообщение для отображения
        stop_event: Событие для остановки анимации
    """
    chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    i = 0
    while not stop_event.is_set():
        sys.stdout.write(f"\r{chars[i % len(chars)]} {message}")
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1
    sys.stdout.write("\r" + " " * (len(message) + 2) + "\r")
    sys.stdout.flush()


def check_service(name: str, port: int, retries: int = 10, delay: int = 3) -> bool:
    """
    Проверяет доступность сервиса через TCP подключение.

    Базовая функция для ожидания готовности сервисов после
    запуска контейнеров. Делает несколько попыток с задержкой.

    Args:
        name: Имя сервиса для логирования
        port: Порт для подключения
        retries: Количество попыток
        delay: Задержка между попытками в секундах

    Returns:
        bool: True если сервис отвечает, False если недоступен
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    for _ in range(retries):
        try:
            sock.connect(("localhost", port))
            sock.close()
            return True
        except:
            print(f"⏳ Ждём {name} на порту {port}...")
            time.sleep(delay)
    return False


def check_services():
    """
    Проверяет готовность всех инфраструктурных сервисов.

    Вызывается после docker-compose up для ожидания полной
    готовности Redis, RabbitMQ и PostgreSQL. Использует
    разное количество попыток для разных сервисов.

    Returns:
        bool: True если все сервисы готовы, False при таймауте

    Note:
        PostgreSQL получает 30 попыток, остальные по 5
    """
    services_config = {
        "Redis": ("REDIS_PORT", 5),
        "RabbitMQ": ("RABBITMQ_UI_PORT", 20),
        "PostgreSQL": ("POSTGRES_PORT", 30),
    }

    for service_name, (port_key, retries) in services_config.items():
        port = get_port(port_key)
        if not check_service(service_name, port, retries):
            print(f"❌ {service_name} не доступен на порту {port}!")
            return False
    return True


def get_postgres_container_name() -> str:
    """
    Определяет имя контейнера PostgreSQL или fallback для прямого подключения.

    Пытается найти запущенный контейнер через docker ps с фильтром по имени.
    Если Docker недоступен или контейнер не найден - возвращает "postgres"
    для прямого подключения к локальной БД.

    Returns:
        str: Имя контейнера PostgreSQL или "postgres" для прямого подключения

    Note:
        Используется в create_database() для выбора метода подключения
    """
    try:
        # Проверяем, доступен ли Docker
        which_result = subprocess.run(
            ["which", "docker"], capture_output=True, text=True
        )
        if which_result.returncode != 0:
            print("ℹ️ Docker не найден, используем прямое подключение к PostgreSQL")
            return "postgres"  # Стандартное имя для прямого подключения

        result = subprocess.run(
            ["docker", "ps", "--filter", "name=postgres", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=True,
        )
        containers = [name for name in result.stdout.strip().split("\n") if name]
        if not containers:
            print(
                "⚠️ Контейнер PostgreSQL не найден через Docker, используем прямое подключение"
            )
            return "postgres"
        return containers[0]  # Берем первый найденный контейнер
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Ошибка при поиске контейнера PostgreSQL через Docker: {e}")
        return "postgres"
    except Exception as e:
        print(f"⚠️ Непредвиденная ошибка: {e}")
        return "postgres"


def create_database():
    """
    Создаёт базу данных если она не существует.

    Поддерживает два режима:
    1. Через Docker exec в контейнер PostgreSQL
    2. Прямое подключение через psql (если Docker недоступен)

    Получает настройки из .env.dev, проверяет существование БД
    через SQL запрос, создаёт если отсутствует.

    Returns:
        bool: True при успехе, False при ошибке

    Note:
        Использует PGPASSWORD для передачи пароля в psql
    """
    print("🛠️ Проверяем наличие базы данных...")

    # Получаем данные из переменных окружения
    db_config = load_env_vars()

    # Получаем имя контейнера PostgreSQL динамически
    postgres_container = get_postgres_container_name()
    print(f"🔍 Используем PostgreSQL: {postgres_container}")

    # Извлекаем настройки БД
    user = db_config.get("POSTGRES_USER", "postgres")
    password = db_config.get("POSTGRES_PASSWORD", "")
    host = db_config.get("POSTGRES_HOST", "localhost")
    port = db_config.get("POSTGRES_PORT", "5432")
    db_name = db_config.get("POSTGRES_DB", "aichat_db")

    try:
        # Проверяем, доступен ли Docker
        which_docker = subprocess.run(["which", "docker"], capture_output=True)
        docker_available = which_docker.returncode == 0

        if docker_available:
            # Метод с использованием Docker
            check_db_inside = subprocess.run(
                [
                    "docker",
                    "exec",
                    "-i",
                    postgres_container,
                    "psql",
                    "-U",
                    user,
                    "-c",
                    f"SELECT 1 FROM pg_database WHERE datname = '{db_name}';",
                ],
                capture_output=True,
                text=True,
            )

            if "1 row" not in check_db_inside.stdout:
                print(
                    f"🛠️ База данных {db_name} не найдена внутри контейнера, создаём..."
                )
                create_cmd = [
                    "docker",
                    "exec",
                    "-i",
                    postgres_container,
                    "psql",
                    "-U",
                    user,
                    "-c",
                    f"CREATE DATABASE {db_name};",
                ]
                subprocess.run(create_cmd, check=True)
                print(f"✅ База данных {db_name} создана внутри контейнера!")
            else:
                print(f"✅ База данных {db_name} существует внутри контейнера!")
        else:
            # Прямое подключение через psql
            print(f"🔄 Проверяем БД напрямую через psql...")

            # Формируем команду для проверки существования БД
            psql_command = f"psql -U {user} -h {host} -p {port}"
            if password:
                # Установка переменной окружения PGPASSWORD для передачи пароля
                env = os.environ.copy()
                env["PGPASSWORD"] = password
            else:
                env = os.environ.copy()

            # Проверяем существование БД
            check_db = subprocess.run(
                f"{psql_command} -c \"SELECT 1 FROM pg_database WHERE datname = '{db_name}';\"",
                shell=True,
                env=env,
                capture_output=True,
                text=True,
            )

            if "1 row" not in check_db.stdout:
                print(f"🛠️ База данных {db_name} не найдена, создаём...")
                create_cmd = f'{psql_command} -c "CREATE DATABASE {db_name};"'
                subprocess.run(create_cmd, shell=True, env=env, check=True)
                print(f"✅ База данных {db_name} создана!")
            else:
                print(f"✅ База данных {db_name} существует!")

        # Выводим информацию о подключении
        dsn = f"postgresql://{user}:*******@{host}:{port}/{db_name}"
        print(f"🔄 Информация о подключении к БД: {dsn} (пароль скрыт)")

        return True
    except Exception as e:
        print(f"❌ Ошибка при работе с базой данных: {e}")
        return False


def start_infrastructure():
    """
    Главная функция запуска инфраструктуры разработки.

    Полный цикл подготовки окружения:
    1. Проверка занятости портов из .env.dev
    2. Валидация Docker daemon
    3. Остановка старых контейнеров (down --remove-orphans)
    4. Очистка volumes
    5. Поиск свободных портов для всех сервисов
    6. Запуск контейнеров с новыми портами
    7. Ожидание готовности сервисов
    8. Выполнение миграций БД
    9. Вывод адресов сервисов

    Returns:
        bool: True при успешном запуске, False при ошибках

    Raises:
        DockerDaemonNotRunningError: Проблемы с Docker
        DockerContainerConflictError: Конфликты контейнеров
    """
    print("🚀 Запускаем инфраструктуру...")

    env_vars = load_env_vars()

    busy_ports = []
    for service, default_port in DEFAULT_PORTS.items():
        # Получаем порт из .env.dev или используем дефолтный
        port = int(env_vars.get(f"{service}_PORT", default_port))
        if not is_port_free(port):
            busy_ports.append(f"{service}: {port}")

    if busy_ports:
        print("❌ Следующие порты заняты:")
        for port_info in busy_ports:
            print(f"   - {port_info}")
        print("💡 Останови процессы на этих портах или измени порты в .env.dev")
        return False

    try:
        # Проверяем статус Docker
        try:
            docker_info = subprocess.run(
                ["docker", "info"], capture_output=True, text=True, check=True
            )
            print("✅ Docker запущен и работает")
        except subprocess.CalledProcessError as e:
            print("❌ Проблема с Docker:")
            if "permission denied" in str(e.stderr).lower():
                print(
                    "💡 Нет прав доступа к Docker. Попробуйте запустить от администратора."
                )
            elif "cannot connect to the docker daemon" in str(e.stderr).lower():
                print("💡 Docker Daemon не отвечает. Проверьте что:")
                print("   1. Docker Desktop точно запущен")
                print("   2. Служба Docker Engine работает")
                print("   3. Нет конфликтов с WSL или другими службами")
            raise DockerDaemonNotRunningError()

        # Проверяем запущенные контейнеры
        print("🔍 Проверяем запущенные контейнеры...")
        ps_result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=True,
        )
        if ps_result.stdout.strip():
            print("⚠️ Найдены запущенные контейнеры:")
            for container in ps_result.stdout.strip().split("\n"):
                print(f"   - {container}")

        # Убиваем все контейнеры
        try:
            run_compose_command("down --remove-orphans")
        except subprocess.CalledProcessError as e:
            error_output = str(e)
            if (
                "docker daemon is not running" in error_output
                or "pipe/docker_engine" in error_output
            ):
                raise DockerDaemonNotRunningError()
            raise

        # Очищаем тома
        try:
            subprocess.run(["docker", "volume", "prune", "-f"], check=True)
        except subprocess.CalledProcessError as e:
            error_output = str(e)
            if (
                "docker daemon is not running" in error_output
                or "pipe/docker_engine" in error_output
            ):
                raise DockerDaemonNotRunningError()
            raise

        # Получаем свободные порты
        ports = {
            service: get_available_port(default_port)
            for service, default_port in DEFAULT_PORTS.items()
        }

        # Используем порты в docker-compose через переменные окружения
        env = {f"{service}_PORT": str(port) for service, port in ports.items()}
        # Запуск контейнеров с loader
        stop_loader = threading.Event()
        loader_thread = threading.Thread(target=show_loader, args=("", stop_loader))
        loader_thread.start()

        try:
            run_compose_command(["up", "-d"], COMPOSE_FILE_WITHOUT_BACKEND, env=env)
        except subprocess.CalledProcessError as e:
            error_output = str(e)
            if (
                "docker daemon is not running" in error_output
                or "pipe/docker_engine" in error_output
            ):
                raise DockerDaemonNotRunningError()
            elif (
                "Conflict" in error_output
                and "is already in use by container" in error_output
            ):
                # Извлекаем имя контейнера из сообщения об ошибке
                import re

                container_match = re.search(
                    r'The container name "([^"]+)"', error_output
                )
                container_name = container_match.group(1) if container_match else None
                raise DockerContainerConflictError(container_name)
            raise
        finally:
            stop_loader.set()
            loader_thread.join()
            print("✅ Контейнеры запущены!")

        # Ждем доступности сервисов
        check_services()

        # Запускаем миграции после успешного поднятия PostgreSQL
        print("📦 Запускаем миграции...")
        migrate()
        print("✅ Миграции выполнены!")

        print("\n" + "=" * 60)
        print("🎯 ИНФРАСТРУКТУРА ГОТОВА")
        print("=" * 60)

        print("\n📡 СЕРВИСЫ:")
        print(f"📊 FastAPI Swagger:    http://localhost:{ports['FASTAPI']}/docs")
        print(f"🐰 RabbitMQ:       http://localhost:{ports['RABBITMQ_UI']}")
        print(f"🗄️ PostgreSQL:        localhost:{ports['POSTGRES']}")
        print(f"📦 Redis:             localhost:{ports['REDIS']}")

        print("\n🔧 АДМИН ПАНЕЛИ:")
        print(f"🔍 PgAdmin:           http://localhost:{ports['PGADMIN']}")
        print(f"📊 Redis Commander:    http://localhost:{ports['REDIS_COMMANDER']}")

        print("\n🔑 ДОСТУПЫ:")
        print(
            f"🔍 PgAdmin:           {env_vars.get('PGADMIN_DEFAULT_EMAIL', 'admin@admin.com')} / {env_vars.get('PGADMIN_DEFAULT_PASSWORD', 'admin')}"
        )
        print(
            f"🐰 RabbitMQ:          {env_vars.get('RABBITMQ_USER', 'guest')} / {env_vars.get('RABBITMQ_PASS', 'guest')}"
        )
        print(
            f"🗄️ PostgreSQL:        {env_vars.get('POSTGRES_USER', 'postgres')} / {env_vars.get('POSTGRES_PASSWORD', 'postgres')}"
        )

        return True
    except DockerDaemonNotRunningError as e:
        print(f"❌ {e}")
        print("💡 Запусти Docker Desktop и попробуй снова, олух.")
        return False
    except DockerContainerConflictError as e:
        print(f"❌ {e}")
        print("💡 Выполни следующую команду для удаления конфликтующих контейнеров:")
        print("```")
        print("docker rm -f $(docker ps -aq)")
        print("```")
        return False
    except Exception as e:
        print(f"❌ Ошибка при запуске инфраструктуры: {e}")
        return False


def setup():
    """
    Настройка окружения разработки через системные скрипты.

    Выбирает и запускает соответствующий скрипт установки
    в зависимости от операционной системы:
    - Windows: scripts/setup.ps1 через PowerShell
    - Unix/Linux: scripts/setup.sh через Bash

    Note:
        Скрипты должны содержать установку зависимостей,
        создание виртуального окружения, копирование .env файлов
    """
    system = platform.system()
    if system == "Windows":
        subprocess.run(["powershell", "-File", "scripts/setup.ps1"], check=True)
    else:
        subprocess.run(["bash", "scripts/setup.sh"], check=True)


def activate():
    """
    Активация виртуального окружения через системные скрипты.

    Запускает платформо-специфичные скрипты активации:
    - Windows: scripts/activate.ps1 через PowerShell
    - Unix/Linux: scripts/activate.sh через Bash

    Note:
        Обычно вызывается после setup() для подготовки
        окружения к разработке
    """
    system = platform.system()
    if system == "Windows":
        subprocess.run(["powershell", "-File", "scripts/activate.ps1"], check=True)
    else:
        subprocess.run(["bash", "scripts/activate.sh"], check=True)


def dev(port: Optional[int] = None):
    """
    Основная команда для разработки - запуск полного стека.

    Выполняет полный цикл подготовки и запуска:
    1. start_infrastructure() - поднимает всю инфраструктуру
    2. find_free_port() - находит свободный порт для FastAPI
    3. uvicorn.run() - запускает сервер с hot reload

    Args:
        port: Конкретный порт для FastAPI. Если None - автопоиск

    Note:
        При ошибке инфраструктуры прерывает выполнение.
        Сервер запускается с debug логами и автоперезагрузкой
    """

    # Запускаем инфраструктуру
    if not start_infrastructure():
        return

    if port is None:
        port = find_free_port()

    print("\n" + "=" * 60)
    print("🚀 ЗАПУСК FASTAPI СЕРВЕРА")
    print("=" * 60)
    print(f"🌐 Адрес: http://localhost:{port}")
    print(f"📚 Документация: http://localhost:{port}/docs")
    print(f"🔄 Hot Reload: включён")
    print("=" * 60 + "\n")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="debug",
        access_log=False,
    )


def serve(port: Optional[int] = None):
    """
    Запуск только FastAPI сервера без инфраструктуры.

    Альтернатива dev() когда инфраструктура уже запущена
    или используется внешняя. Запускает uvicorn через subprocess
    с продакшн настройками (proxy-headers, forwarded-allow-ips).

    Args:
        port: Порт для сервера. Если None - автопоиск

    """
    if port is None:
        port = find_free_port()

    print(f"🚀 Запускаем сервер на порту {port}")
    subprocess.run(
        [
            "uvicorn",
            "app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            str(port),
            "--proxy-headers",
            "--forwarded-allow-ips=*",
        ],
        check=True,
    )


def migrate():
    """
    Применение миграций базы данных через Alembic.

    Выполняет команду 'alembic upgrade head' для применения
    всех неприменённых миграций. Используется автоматически
    в start_infrastructure() и start_all().

    Raises:
        subprocess.CalledProcessError: При ошибках миграции

    Note:
        Требует настроенного alembic.ini и доступной БД
    """
    subprocess.run(["alembic", "upgrade", "head"], check=True)


def format():
    """
    Автоматическое форматирование кода.

    Последовательно запускает:
    1. black app/ - форматирование Python кода
    2. isort app/ - сортировка импортов

    Raises:
        subprocess.CalledProcessError: При ошибках форматирования

    Note:
        Изменяет файлы на месте без подтверждения
    """
    subprocess.run(["black", "app/"], check=True)
    subprocess.run(["isort", "app/"], check=True)


def check():
    """
    Статическая проверка качества кода.

    Выполняет проверки через mypy и flake8 с группировкой
    ошибок по типам для удобного анализа:
    - MyPy: типы, аргументы, возвращаемые значения
    - Flake8: длинные строки, неиспользуемые переменные, стиль

    Returns:
        bool: True если проверки прошли без ошибок

    Note:
        Продолжает выполнение даже при ошибках одного из инструментов
    """
    mypy_success = True
    flake8_success = True

    # Проверка mypy
    try:
        mypy_result = subprocess.run(
            ["mypy", "app/"], capture_output=True, text=True, check=True
        )
        mypy_errors = mypy_result.stdout.split("\n")

        mypy_error_groups = {
            "error: Incompatible": "Несовместимые типы",
            "error: Name": "Ошибки именования",
            "error: Missing": "Отсутствующие типы",
            "error: Argument": "Ошибки аргументов",
            "error: Return": "Ошибки возвращаемых значений",
        }

        # Сначала собираем все ошибки в известные группы
        grouped_errors = set()
        for pattern, desc in mypy_error_groups.items():
            matches = [e for e in mypy_errors if pattern in e]
            if matches:
                print(f"\n🔍 MyPy - {desc}:")
                for error in matches:
                    print(f"- {error}")
                    grouped_errors.add(error)

        # Оставшиеся ошибки выводим как "Прочие"
        other_errors = [e for e in mypy_errors if e and e not in grouped_errors]
        if other_errors:
            print("\n🔍 MyPy - Прочие ошибки:")
            for error in other_errors:
                print(f"- {error}")
    except subprocess.CalledProcessError as e:
        print("❌ Найдены ошибки mypy:")
        print(e.stdout)
        mypy_success = False

    # Проверка flake8
    try:
        result = subprocess.run(
            ["flake8", "app/"], capture_output=True, text=True, check=True
        )
        flake8_errors = result.stdout.split("\n")

        # Группируем ошибки по типу
        error_groups = {
            "E501": "Длинные строки",
            "F821": "Неопределенные переменные",
            "F841": "Неиспользуемые переменные",
            "W605": "Некорректные escape-последовательности",
            "E262": "Неправильные комментарии",
        }

        # Собираем известные ошибки
        grouped_errors = set()
        for code, desc in error_groups.items():
            matches = [e for e in flake8_errors if code in e]
            if matches:
                print(f"\n🔍 Flake8 - {desc}:")
                for error in matches:
                    print(f"- {error.split(':')[0]}")
                    grouped_errors.add(error)

        # Выводим оставшиеся ошибки
        other_errors = [e for e in flake8_errors if e and e not in grouped_errors]
        if other_errors:
            print("\n🔍 Flake8 - Прочие ошибки:")
            for error in other_errors:
                print(f"- {error.split(':')[0]}")

    except subprocess.CalledProcessError as e:
        print("❌ Найдены ошибки flake8: ")
        print(e.stdout)
        flake8_success = False

    return mypy_success and flake8_success


async def create_superuser():
    await database_client.connect()

    session_gen = get_db_session()
    session = await anext(session_gen)
    try:
        username = input("Enter username: ")
        email = input("Enter email: ")
        password = input("Enter password: ")

        hashed_password = pwd_context.hash(password)

        superuser = UserModel(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_verified=True,
            role=UserRole.ADMIN,
        )
        session.add(superuser)
        await session.commit()
        print(f"✅ Superuser '{username}' успешно создан!")
    finally:
        await session_gen.aclose()
        await database_client.close()


def run_create_superuser():
    asyncio.run(create_superuser())


def lint():
    """
    Полный цикл линтинга: форматирование + проверка.

    Последовательно вызывает format() и check() для
    автоматического исправления стиля и проверки качества кода.

    Note:
        Удобная команда для подготовки кода к коммиту
    """
    format()
    check()


def test(
    path: str = "tests/",
    marker: str = None,
    verbose: bool = True,
    output_file: str = None,
):
    """
    Запуск тестов с фильтрацией.

    Args:
        path: Путь к тестам или конкретному файлу
        marker: Маркер для фильтрации (@pytest.mark.unit и т.д.)
        verbose: Подробный вывод
        output_file: Файл для сохранения результатов
    """
    print("🧪 Подготовка тестового окружения...")

    if not create_test_database():
        print("❌ Не удалось создать тестовую базу данных")
        return

    env = os.environ.copy()
    env["DEV_ENV_FILE"] = ".env.test"

    cmd = ["pytest", path]

    if verbose:
        cmd.append("-v")

    if marker:
        cmd.extend(["-m", marker])

    cmd.append("--tb=short")  # Короткий traceback

    print(f"🚀 Запуск тестов: {' '.join(cmd)}")

    try:
        if output_file:
            with open(output_file, "w") as f:
                subprocess.run(
                    cmd, env=env, stdout=f, stderr=subprocess.STDOUT, check=True
                )
        else:
            subprocess.run(cmd, env=env, check=True)
    except subprocess.CalledProcessError:
        pass


# def create_test_database():
#     """
#     Создает тестовую базу данных для pytest.

#     Использует настройки из .env.dev, но создает базу с суффиксом _test.
#     Поддерживает как Docker, так и прямое подключение к PostgreSQL.

#     Returns:
#         bool: True при успехе, False при ошибке
#     """
#     print("🛠️ Создаю тестовую базу данных...")

#     # Получаем данные из переменных окружения
#     db_config = load_env_vars()

#     # Получаем имя контейнера PostgreSQL динамически
#     postgres_container = get_postgres_container_name()
#     print(f"🔍 Используем PostgreSQL: {postgres_container}")

#     # Извлекаем настройки БД
#     user = db_config.get('POSTGRES_USER', 'postgres')
#     password = db_config.get('POSTGRES_PASSWORD', '')
#     host = db_config.get('POSTGRES_HOST', 'localhost')
#     port = db_config.get('POSTGRES_PORT', '5432')
#     db_name = db_config.get('POSTGRES_DB', 'gidrator_db')
#     test_db_name = f"{db_name}_test"

#     try:
#         # Проверяем, доступен ли Docker
#         which_docker = subprocess.run(["which", "docker"], capture_output=True)
#         docker_available = which_docker.returncode == 0

#         if docker_available and postgres_container != "postgres":
#             # Метод с использованием Docker
#             print(f"🐳 Создаю тестовую БД через Docker контейнер: {postgres_container}")

#             # Удаляем существующую тестовую БД если есть
#             subprocess.run(
#                 ["docker", "exec", "-i", postgres_container, "psql", "-U", user, "-c",
#                 f"DROP DATABASE IF EXISTS {test_db_name};"],
#                 capture_output=True, text=True
#             )

#             # Создаем тестовую БД
#             create_cmd = [
#                 "docker", "exec", "-i", postgres_container, "psql", "-U", user, "-c",
#                 f"CREATE DATABASE {test_db_name};"
#             ]
#             result = subprocess.run(create_cmd, capture_output=True, text=True)

#             if result.returncode == 0:
#                 print(f"✅ Тестовая база данных {test_db_name} создана в контейнере!")
#             else:
#                 print(f"❌ Ошибка создания БД в контейнере: {result.stderr}")
#                 return False
#         else:
#             # Прямое подключение через psql
#             print(f"🔄 Создаю тестовую БД напрямую через psql...")

#             # Формируем команду для работы с БД
#             psql_command = f"psql -U {user} -h {host} -p {port}"
#             if password:
#                 env = os.environ.copy()
#                 env["PGPASSWORD"] = password
#             else:
#                 env = os.environ.copy()

#             # Удаляем существующую тестовую БД если есть
#             drop_cmd = f"{psql_command} -c \"DROP DATABASE IF EXISTS {test_db_name};\""
#             subprocess.run(drop_cmd, shell=True, env=env, capture_output=True)

#             # Создаем тестовую БД
#             create_cmd = f"{psql_command} -c \"CREATE DATABASE {test_db_name};\""
#             result = subprocess.run(create_cmd, shell=True, env=env, capture_output=True, text=True)

#             if result.returncode == 0:
#                 print(f"✅ Тестовая база данных {test_db_name} создана!")
#             else:
#                 print(f"❌ Ошибка создания тестовой БД: {result.stderr}")
#                 return False

#         # Выводим информацию о подключении
#         test_dsn = f"postgresql://{user}:*******@{host}:{port}/{test_db_name}"
#         print(f"🔄 Тестовая БД доступна: {test_dsn}")

#         return True
#     except Exception as e:
#         print(f"❌ Ошибка при создании тестовой базы данных: {e}")
#         return False


async def create_test_database_async():
    """
    Создает тестовую базу данных используя asyncpg (без psql).
    """
    print("🛠️ Создаю тестовую базу данных...")

    db_config = load_env_vars()

    if not db_config:
        print("❌ Не удалось загрузить конфигурацию БД")
        return False

    user = db_config.get("POSTGRES_USER", "postgres")
    password = db_config.get("POSTGRES_PASSWORD", "")
    host = db_config.get("POSTGRES_HOST", "localhost")
    port = int(db_config.get("POSTGRES_PORT", "5432"))
    db_name = db_config.get("POSTGRES_DB", "gidrator_db")
    test_db_name = f"{db_name}_test"

    print(f"🔍 Подключение к {host}:{port} как {user}")

    try:
        # Подключаемся к postgres БД для создания тестовой БД
        conn = await asyncpg.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database="postgres",  # Подключаемся к системной БД
        )

        # Удаляем существующую тестовую БД если есть
        await conn.execute(f'DROP DATABASE IF EXISTS "{test_db_name}"')
        print(f"🗑️ Удалена существующая БД {test_db_name} (если была)")

        # Создаем тестовую БД
        await conn.execute(f'CREATE DATABASE "{test_db_name}"')
        print(f"✅ Тестовая база данных {test_db_name} создана!")

        await conn.close()

        # Выводим информацию о подключении
        test_dsn = f"postgresql://{user}:*******@{host}:{port}/{test_db_name}"
        print(f"🔄 Тестовая БД доступна: {test_dsn}")
        return True

    except Exception as e:
        print(f"❌ Ошибка при создании тестовой базы данных: {e}")
        return False


def create_test_database():
    """Синхронная обертка для асинхронной функции"""
    return asyncio.run(create_test_database_async())


def start_all():
    """
    Быстрый старт: миграции + сервер без инфраструктуры.

    Альтернатива dev() когда инфраструктура уже запущена.
    Применяет миграции и запускает сервер через serve().

    Note:
        Не проверяет доступность БД перед миграциями
    """
    migrate()
    serve()

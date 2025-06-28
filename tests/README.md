# Документация по тестированию

## Структура тестов

```
tests/
├── conftest.py                    # Общие фикстуры для всех тестов
├── utils.py                       # Утилиты для тестов
├── unit/                          # Unit тесты (изолированные функции/классы)
├── integration/                   # Integration тесты (взаимодействие компонентов с моками)
├── functional/                    # Functional тесты (полный цикл с реальной БД)
├── security/                      # Security тесты
├── performance/                   # Performance тесты
└── e2e/                          # End-to-end тесты
```

## Типы тестов

### 1. Unit тесты
- **Цель**: Тестирование изолированных функций/классов
- **Моки**: Все внешние зависимости
- **Скорость**: Очень быстрые (< 1ms)
- **Когда использовать**: Тестирование бизнес-логики, утилит, валидаторов

```python
def test_password_hash():
    """Unit тест функции хеширования пароля"""
    password = "SecurePass123!"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True
```

### 2. Integration тесты
- **Цель**: Тестирование взаимодействия между компонентами
- **Моки**: Внешние сервисы (БД, email, Redis)
- **Скорость**: Быстрые (< 100ms)
- **Когда использовать**: Тестирование HTTP контрактов, валидации, обработки ошибок

```python
@patch('app.services.registration.RegisterService')
async def test_register_endpoint(mock_service, client):
    """Integration тест роутера регистрации"""
    mock_service.return_value.create_user.return_value = {"success": True}
    response = await client.post("/register", json=user_data)
    assert response.status_code == 200
```

### 3. Functional тесты
- **Цель**: Тестирование полного цикла бизнес-процессов
- **Моки**: Только внешние системы (email, платежи)
- **Скорость**: Медленные (100ms - 1s)
- **Когда использовать**: Тестирование бизнес-логики, работы с БД

```python
async def test_user_registration_flow(client, db_session):
    """Functional тест полного цикла регистрации"""
    response = await client.post("/register", json=user_data)
    assert response.status_code == 200

    # Проверяем что пользователь создался в БД
    user = await db_session.get(User, user_data["email"])
    assert user is not None
```

## Фикстуры в conftest.py

### test_engine
- Создает тестовую БД PostgreSQL
- Создает все таблицы
- Удаляет БД после тестов

### db_session
- Создает изолированную сессию для каждого теста
- Использует транзакции с rollback для изоляции
- Каждый тест получает чистую БД

### client
- HTTP клиент для тестирования API
- Подменяет get_db_session на тестовую сессию
- Используется в functional тестах

### auth_client
- HTTP клиент с мокированной авторизацией
- Автоматически "авторизует" запросы
- Используется для тестирования защищенных endpoints

### mock_messaging
- Автоматически мокирует систему сообщений
- Предотвращает отправку реальных email в тестах
- Применяется ко всем тестам (autouse=True)

## Запуск тестов

```bash
# Все тесты
pytest

# Только быстрые тесты (unit + integration)
pytest -m "not functional"

# Только functional тесты
pytest -m functional

# Только integration тесты
pytest -m integration

# Конкретный файл
pytest tests/functional/routes/test_registration.py

# С покрытием кода
pytest --cov=app

# Параллельный запуск
pytest -n auto
```

## Маркеры тестов

```python
@pytest.mark.unit          # Unit тесты
@pytest.mark.integration   # Integration тесты
@pytest.mark.functional    # Functional тесты
@pytest.mark.security      # Security тесты
@pytest.mark.performance   # Performance тесты
@pytest.mark.e2e          # End-to-end тесты
@pytest.mark.slow         # Медленные тесты
```

## Лучшие практики

### 1. Именование тестов
```python
def test_should_create_user_when_valid_data_provided():
    """Описательное имя теста"""
    pass
```

### 2. Структура теста (AAA)
```python
async def test_user_registration():
    # Arrange - подготовка данных
    user_data = {"username": "test", "email": "test@example.com"}

    # Act - выполнение действия
    response = await client.post("/register", json=user_data)

    # Assert - проверка результата
    assert response.status_code == 200
```

### 3. Изоляция тестов
- Каждый тест должен быть независимым
- Не полагайтесь на порядок выполнения тестов
- Используйте фикстуры для подготовки данных

### 4. Моки
```python
# ✅ Хорошо - мокируем внешние зависимости
@patch('app.services.email.EmailService.send')
async def test_registration_sends_email(mock_send):
    pass

# ❌ Плохо - мокируем внутреннюю логику
@patch('app.services.registration.RegisterService._validate_user')
async def test_registration(mock_validate):
    pass
```

### 5. Тестовые данные
```python
# ✅ Используйте фабрики/утилиты
def create_test_user_data(**overrides):
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "SecurePass123!"
    }
    data.update(overrides)
    return data

# ✅ Параметризованные тесты
@pytest.mark.parametrize("password,should_fail", [
    ("123", True),
    ("SecurePass123!", False)
])
def test_password_validation(password, should_fail):
    pass
```

## Отладка тестов

```bash
# Запуск с выводом print
pytest -s

# Остановка на первой ошибке
pytest -x

# Подробный вывод
pytest -v

# Отладка конкретного теста
pytest tests/test_file.py::test_function -s -v
```

## Покрытие кода

```bash
# Генерация отчета о покрытии
pytest --cov=app --cov-report=html

# Просмотр отчета
open htmlcov/index.html
```

## Примеры использования

### Тестирование с реальной БД
```python
async def test_user_creation(client, db_session):
    response = await client.post("/users", json=user_data)

    # Проверяем ответ API
    assert response.status_code == 201

    # Проверяем данные в БД
    user = await db_session.get(User, response.json()["id"])
    assert user.username == user_data["username"]
```

### Тестирование с моками
```python
@patch('app.services.email.EmailService')
async def test_registration_with_email(mock_email, client):
    mock_email.return_value.send_verification.return_value = True

    response = await client.post("/register", json=user_data)

    assert response.status_code == 200
    mock_email.return_value.send_verification.assert_called_once()
```

### Тестирование авторизации
```python
async def test_protected_endpoint(auth_client):
    # auth_client автоматически авторизован
    response = await auth_client.get("/protected")
    assert response.status_code == 200

async def test_unauthorized_access(client):
    # client без авторизации
    response = await client.get("/protected")
    assert response.status_code == 401
```

### Тестирование ошибок
```python
async def test_validation_error(client):
    invalid_data = {"email": "invalid-email"}
    response = await client.post("/register", json=invalid_data)

    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(err["loc"] == ["email"] for err in errors)
```

## Частые проблемы и решения

### 1. Тесты падают из-за порядка выполнения
**Проблема**: Тесты зависят друг от друга
**Решение**: Используйте фикстуры с rollback транзакций

```python
# ❌ Плохо
def test_create_user():
    user = create_user("test@example.com")

def test_user_exists():
    user = get_user("test@example.com")  # Зависит от предыдущего теста
    assert user is not None

# ✅ Хорошо
def test_create_user(db_session):
    user = create_user("test@example.com")
    db_session.add(user)
    await db_session.commit()
    # Автоматический rollback после теста

def test_user_exists(db_session):
    user = create_user("test@example.com")
    db_session.add(user)
    await db_session.commit()

    found_user = await get_user("test@example.com")
    assert found_user is not None
```

### 2. Медленные тесты
**Проблема**: Тесты выполняются долго
**Решение**: Используйте правильные типы тестов

```python
# ❌ Медленно - functional тест для простой валидации
async def test_email_validation(client, db_session):
    response = await client.post("/register", json={"email": "invalid"})
    assert response.status_code == 422

# ✅ Быстро - unit тест
def test_email_validation():
    with pytest.raises(ValidationError):
        UserSchema(email="invalid")
```

### 3. Проблемы с моками
**Проблема**: Моки не работают как ожидается
**Решение**: Правильное указание пути для мокирования

```python
# ❌ Неправильный путь
@patch('app.services.email.EmailService')  # Мокирует в модуле определения

# ✅ Правильный путь
@patch('app.routes.registration.EmailService')  # Мокирует в модуле использования
```

### 4. Проблемы с async/await
**Проблема**: Тесты не работают с асинхронным кодом
**Решение**: Используйте pytest-asyncio

```python
# ❌ Неправильно
def test_async_function():
    result = async_function()  # Возвращает coroutine, не результат

# ✅ Правильно
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result == expected_value
```

### 5. Проблемы с БД в тестах
**Проблема**: Тесты влияют друг на друга через БД
**Решение**: Используйте транзакции с rollback

```python
# conftest.py уже настроен правильно:
@pytest_asyncio.fixture
async def db_session(test_engine):
    connection = await test_engine.connect()
    transaction = await connection.begin()
    session = AsyncSession(bind=connection)

    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()  # Откатывает все изменения
        await connection.close()
```

## Производительность тестов

### Пирамида тестов
```
     /\
    /E2E\     <- Мало, медленные, дорогие
   /____\
  /      \
 /Functional\ <- Средне, проверяют интеграцию
/__________\
/          \
/   Unit     \ <- Много, быстрые, дешевые
/____________\
```

### Рекомендуемое соотношение
- **70%** Unit тесты
- **20%** Integration тесты
- **10%** Functional/E2E тесты

### Оптимизация скорости
```bash
# Параллельный запуск
pip install pytest-xdist
pytest -n auto

# Только быстрые тесты в CI
pytest -m "not slow"

# Кеширование результатов
pytest --cache-clear  # Очистить кеш
```

## Continuous Integration

### GitHub Actions пример
```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov

    - name: Run fast tests
      run: pytest -m "not functional" --cov=app

    - name: Run functional tests
      run: pytest -m functional
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
```

## Мониторинг качества тестов

### Метрики
- **Покрытие кода**: > 80%
- **Время выполнения**: < 5 минут для всех тестов
- **Стабильность**: < 1% flaky тестов

### Инструменты
```bash
# Покрытие кода
pytest --cov=app --cov-report=term-missing

# Профилирование медленных тестов
pytest --durations=10

# Поиск неиспользуемого кода
pip install vulture
vulture app/
```

## Заключение

Правильно организованные тесты:
- ✅ Быстро выполняются
- ✅ Легко поддерживаются
- ✅ Надежно ловят баги
- ✅ Документируют поведение системы
- ✅ Дают уверенность при рефакторинге

Помните: **хорошие тесты - это инвестиция в будущее проекта**.
```

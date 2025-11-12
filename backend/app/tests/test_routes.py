"""Тесты для эндпоинтов проекта"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ============================================================================
# ЭНДПОИНТ: GET /api/text
# ============================================================================


class TestGetRandomText:
    """Тесты для эндпоинта GET /api/text"""

    @pytest.mark.parametrize(
        "lang,difficulty,expected_status",
        [
            ("ru", "easy", 200),
            ("ru", "medium", 200),
            ("ru", "hard", 200),
            ("en", "easy", 200),
            ("en", "medium", 200),
            ("en", "hard", 200),
            ("invalid_lang", "easy", 500),
            ("ru", "invalid_difficulty", 500),
            ("xyz", "xyz", 500),
        ],
    )
    @pytest.mark.asyncio
    async def test_get_random_text_parametrized_valid_combinations(
        self, lang, difficulty, expected_status, async_client, settings
    ):
        """Проверяет, что эндпоинт корректно обрабатывает различные комбинации языков и сложности"""
        response = await async_client.get(
            f"/api/text?lang={lang}&difficulty={difficulty}"
        )

        assert response.status_code == expected_status

        if expected_status == 200:
            data = response.json()
            assert "text" in data
            assert "language" in data
            assert "difficulty" in data
            assert data["language"] == lang
            assert data["difficulty"] == difficulty
        else:
            assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_get_random_text_default_params(self, async_client, settings):
        """
        Тест получения текста с параметрами по умолчанию.
        """
        response = await async_client.get("/api/text")

        assert response.status_code == 200
        data = response.json()

        assert "text" in data
        assert "language" in data
        assert "difficulty" in data

        assert data["text"] is not None
        assert data["text"] != ""
        assert isinstance(data["text"], str)
        assert len(data["text"]) > 0

        assert (
            data["language"] == settings.default_level
            or data["language"] in settings.allowed_languages
        )
        assert data["difficulty"] in settings.allowed_levels

    @pytest.mark.asyncio
    async def test_get_random_text_response_format(self, async_client, settings):
        """Тест формата ответа эндпоинта"""
        response = await async_client.get(
            f"/api/text?lang={settings.allowed_languages[0]}&difficulty={settings.allowed_levels[0]}"
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, dict)
        assert len(data) == 3

        assert isinstance(data["text"], str)
        assert isinstance(data["language"], str)
        assert isinstance(data["difficulty"], str)

        assert len(data["text"]) > 0
        assert len(data["language"]) > 0
        assert len(data["difficulty"]) > 0

    @pytest.mark.asyncio
    async def test_get_random_text_multiple_calls_different_texts(
        self, async_client, settings
    ):
        """Тест на генерацию разных текстов при нескольких вызовах"""
        response1 = await async_client.get("/api/text")
        response2 = await async_client.get("/api/text")

        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        assert data1["text"] != data2["text"]

    @pytest.mark.parametrize(
        "lang,difficulty",
        [
            ("", "easy"),
            ("ru", ""),
            ("", ""),
            (" ", "easy"),
            ("ru", " "),
            ("  ru  ", "  easy  "),
        ],
    )
    @pytest.mark.asyncio
    async def test_get_random_text_boundary_empty_and_whitespace(
        self, lang, difficulty, async_client, settings
    ):
        """Тест граничных значений с пустыми строками и пробелами"""
        response = await async_client.get(
            f"/api/text?lang={lang}&difficulty={difficulty}"
        )

        assert response.status_code in [400, 500]
        assert "detail" in response.json()

    @pytest.mark.parametrize(
        "lang,difficulty",
        [
            ("ru" * 100, "easy"),
            ("ru", "easy" * 100),
            ("a" * 1000, "b" * 1000),
        ],
    )
    @pytest.mark.asyncio
    async def test_get_random_text_boundary_very_long_params(
        self, lang, difficulty, async_client, settings
    ):
        """Тест граничных значений с очень длинными параметрами"""
        response = await async_client.get(
            f"/api/text?lang={lang}&difficulty={difficulty}"
        )

        assert response.status_code in [400, 500]

    @pytest.mark.parametrize(
        "special_chars",
        [
            "ru'; DROP TABLE--",
            "<script>alert('xss')</script>",
            "ru%00easy",
            "ru/../../../etc/passwd",
        ],
    )
    @pytest.mark.asyncio
    async def test_get_random_text_security_injection_attempts(
        self, special_chars, async_client, settings
    ):
        """Тест безопасности - попытки инъекций"""
        response = await async_client.get(
            f"/api/text?lang={special_chars}&difficulty=easy"
        )

        assert response.status_code in [400, 500]
        data = response.json()
        assert "detail" in data
        assert "traceback" not in str(data).lower()

    @pytest.mark.asyncio
    async def test_get_random_text_config_error(self, async_client, settings):
        """Тест на ошибку конфигурации"""
        with patch("backend.app.api.routes.settings") as mock_settings:
            mock_settings.text_generation_config = {}

            response = await async_client.get("/api/text?lang=unknown&difficulty=easy")

            assert response.status_code == 500
            assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_get_random_text_with_mock_word_extractor(
        self, async_client, settings, mock_word_extractor
    ):
        """Тест с мокированным WordExtractor"""
        mock_text = "Это тестовый текст для проверки"
        mock_word_extractor.generate_random_text.return_value = mock_text

        response = await async_client.get(
            f"/api/text?lang={settings.allowed_languages[0]}&difficulty={settings.allowed_levels[0]}"
        )

        assert response.status_code == 200
        assert response.json()["text"] == mock_text


# ============================================================================
# ЭНДПОИНТ: POST /api/test-result
# ============================================================================


class TestSaveTestResult:
    """Тесты для эндпоинта POST /api/test-result"""

    @pytest.mark.parametrize(
        "chars_per_minute,accuracy,time_seconds",
        [
            (0.0, 0.0, 0.0),
            (0.001, 0.001, 0.001),
            (1.0, 1.0, 1.0),
            (100.0, 100.0, 100.0),
            (999.99, 99.99, 3600.0),
            (999999.99, 99.99, 999999.0),
        ],
    )
    @pytest.mark.asyncio
    async def test_save_test_result_boundary_values(
        self,
        chars_per_minute,
        accuracy,
        time_seconds,
        async_client,
        settings,
        mock_user_repository,
        mock_test_result_repository,
        mock_settings,
    ):
        """Параметризованный тест граничных значений"""
        test_data = {
            "user_id": "test_user_123",
            "chars_per_minute": chars_per_minute,
            "accuracy": accuracy,
            "time_seconds": time_seconds,
            "language": settings.allowed_languages[0],
            "difficulty": settings.allowed_levels[0],
        }

        response = await async_client.post("/api/test-result", json=test_data)

        assert response.status_code in [200, 400, 422]

        if response.status_code == 200:
            data = response.json()
            assert "user_id" in data
            assert "test_result_id" in data

    @pytest.mark.asyncio
    async def test_save_test_result_with_empty_user_id(
        self,
        async_client,
        settings,
        mock_user_repository,
        mock_test_result_repository,
        mock_settings,
    ):
        """Тест с пустым user_id (должен быть создан новый)."""
        test_data = {
            "user_id": "",
            "chars_per_minute": 85.5,
            "accuracy": 95.2,
            "time_seconds": 60.0,
            "language": settings.allowed_languages[0],
            "difficulty": settings.allowed_levels[0],
        }

        response = await async_client.post("/api/test-result", json=test_data)
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "test_result_id" in data

    @pytest.mark.parametrize(
        "chars_per_minute,accuracy,time_seconds,expected_status",
        [
            (-50.0, 95.0, 60.0, 400),
            (85.0, -10.0, 60.0, 400),
            (85.0, 95.0, -60.0, 400),
            (-50.0, -10.0, -60.0, 400),
        ],
    )
    @pytest.mark.asyncio
    async def test_save_test_result_negative_values(
        self,
        chars_per_minute,
        accuracy,
        time_seconds,
        expected_status,
        async_client,
        settings,
        mock_user_repository,
        mock_test_result_repository,
        mock_settings,
    ):
        """Тест отрицательных значений"""
        test_data = {
            "user_id": "test_user_123",
            "chars_per_minute": chars_per_minute,
            "accuracy": accuracy,
            "time_seconds": time_seconds,
            "language": settings.allowed_languages[0],
            "difficulty": settings.allowed_levels[0],
        }

        response = await async_client.post("/api/test-result", json=test_data)

        assert response.status_code in [400, 422]

    @pytest.mark.parametrize(
        "field",
        [
            "chars_per_minute",
            "accuracy",
            "time_seconds",
            "language",
            "difficulty",
        ],
    )
    @pytest.mark.asyncio
    async def test_save_test_result_missing_required_fields(
        self,
        field,
        async_client,
        settings,
        mock_user_repository,
        mock_test_result_repository,
        mock_settings,
    ):
        """Тест отсутствующих обязательных полей"""
        test_data = {
            "user_id": "test_user_123",
            "chars_per_minute": 85.5,
            "accuracy": 95.2,
            "time_seconds": 60.0,
            "language": settings.allowed_languages[0],
            "difficulty": settings.allowed_levels[0],
        }

        del test_data[field]

        response = await async_client.post("/api/test-result", json=test_data)
        assert response.status_code in [400, 422]

    @pytest.mark.parametrize(
        "invalid_type_field,invalid_value",
        [
            ("chars_per_minute", "invalid_string"),
            ("accuracy", "not_a_number"),
            ("time_seconds", "sixty"),
        ],
    )
    @pytest.mark.asyncio
    async def test_save_test_result_invalid_data_types(
        self,
        invalid_type_field,
        invalid_value,
        async_client,
        settings,
        mock_user_repository,
        mock_test_result_repository,
        mock_settings,
    ):
        """Тест невалидных типов данных"""
        test_data = {
            "user_id": "test_user_123",
            "chars_per_minute": 85.5,
            "accuracy": 95.2,
            "time_seconds": 60.0,
            "language": settings.allowed_languages[0],
            "difficulty": settings.allowed_levels[0],
        }

        test_data[invalid_type_field] = invalid_value

        response = await async_client.post("/api/test-result", json=test_data)
        assert response.status_code in [400, 422]

    @pytest.mark.parametrize(
        "malicious_user_id",
        [
            "user'; DROP TABLE users;--",
            "<script>alert('xss')</script>",
            "user%00null",
            "user/../../../etc/passwd",
            "user%27 OR %271%27=%271",
            "user' OR '1'='1",
        ],
    )
    @pytest.mark.asyncio
    async def test_save_test_result_security_injection_user_id(
        self,
        malicious_user_id,
        async_client,
        settings,
        mock_user_repository,
        mock_test_result_repository,
        mock_settings,
    ):
        """Тест безопасности - инъекции в user_id"""
        test_data = {
            "user_id": malicious_user_id,
            "chars_per_minute": 85.5,
            "accuracy": 95.2,
            "time_seconds": 60.0,
            "language": settings.allowed_languages[0],
            "difficulty": settings.allowed_levels[0],
        }

        response = await async_client.post("/api/test-result", json=test_data)
        data = response.json()
        assert "traceback" not in str(data).lower()

    @pytest.mark.parametrize(
        "malicious_language",
        [
            "'; DROP TABLE--",
            "<img src=x onerror=alert('xss')>",
            "ru%00en",
        ],
    )
    @pytest.mark.asyncio
    async def test_save_test_result_security_injection_language(
        self,
        malicious_language,
        async_client,
        settings,
        mock_user_repository,
        mock_test_result_repository,
        mock_settings,
    ):
        """Тест безопасности - инъекции в language"""
        test_data = {
            "user_id": "test_user_123",
            "chars_per_minute": 85.5,
            "accuracy": 95.2,
            "time_seconds": 60.0,
            "language": malicious_language,
            "difficulty": settings.allowed_levels[0],
        }

        response = await async_client.post("/api/test-result", json=test_data)
        data = response.json()
        assert "traceback" not in str(data).lower()

    @pytest.mark.asyncio
    async def test_save_test_result_with_valid_user_id(
        self,
        async_client,
        settings,
        mock_user_repository,
        mock_test_result_repository,
        mock_settings,
    ):
        """Тест сохранения результата с валидным user_id"""
        test_data = {
            "user_id": "123",
            "chars_per_minute": 85.5,
            "accuracy": 95.2,
            "time_seconds": 60.0,
            "language": settings.allowed_languages[0],
            "difficulty": settings.allowed_levels[0],
        }

        response = await async_client.post("/api/test-result", json=test_data)

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "123"
        assert data["test_result_id"] == "test_result_1"

    @pytest.mark.asyncio
    async def test_save_test_result_database_error(
        self,
        async_client,
        settings,
        mock_user_repository,
        mock_settings,
    ):
        """Тест на ошибку базы данных"""
        test_data = {
            "user_id": "123",
            "chars_per_minute": 80.0,
            "accuracy": 92.0,
            "time_seconds": 60.0,
            "language": settings.allowed_languages[0],
            "difficulty": settings.allowed_levels[0],
        }

        with patch("backend.app.api.routes.TestResultRepository") as mock_class:
            mock_repo = AsyncMock()
            mock_repo.create.side_effect = Exception("Database connection error")
            mock_class.return_value = mock_repo

            response = await async_client.post("/api/test-result", json=test_data)

            assert response.status_code == 500
            assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_save_test_result_response_format(
        self,
        async_client,
        settings,
        mock_user_repository,
        mock_test_result_repository,
        mock_settings,
    ):
        """Тест формата ответа"""
        test_data = {
            "user_id": "123",
            "chars_per_minute": 85.5,
            "accuracy": 95.2,
            "time_seconds": 60.0,
            "language": settings.allowed_languages[0],
            "difficulty": settings.allowed_levels[0],
        }

        response = await async_client.post("/api/test-result", json=test_data)

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, dict)
        assert "user_id" in data
        assert "test_result_id" in data
        assert len(data) == 2

        assert isinstance(data["user_id"], str)
        assert isinstance(data["test_result_id"], str)


# ============================================================================
# ЭНДПОИНТ: GET /api/statistics/{user_id}
# ============================================================================


class TestGetUserStatistics:
    """Тесты для эндпоинта GET /api/statistics/{user_id}"""

    @pytest.mark.parametrize(
        "user_id,num_results,expected_status",
        [
            ("user_123", 1, 200),
            ("user_456", 5, 200),
            ("user_789", 10, 200),
            ("user_empty", 0, 404),
        ],
    )
    @pytest.mark.asyncio
    async def test_get_statistics_parametrized_various_scenarios(
        self, user_id, num_results, expected_status, async_client, settings
    ):
        """Параметризованный тест различных сценариев"""
        with (
            patch("backend.app.api.routes.TestResultRepository") as mock_repo_class,
            patch("backend.app.api.routes.UserProgressCalculator") as mock_calc,
        ):
            mock_repo = AsyncMock()

            results = []
            for i in range(num_results):
                mock_result = MagicMock()
                mock_result.id = f"result_{i}"
                mock_result.chars_per_minute = 70.0 + i * 2
                mock_result.accuracy = 90.0 + i
                results.append(mock_result)

            mock_repo.get_by_user_id.return_value = results
            if results:
                mock_repo.get_last_result_by_user_id.return_value = results[-1]
                mock_repo.get_user_best_performance.return_value = results[-1]
            mock_repo.get_user_test_result_statistics.return_value = {}
            mock_repo_class.return_value = mock_repo

            mock_calc.calculate_progress.return_value = {}

            response = await async_client.get(f"/api/statistics/{user_id}")

            assert response.status_code == expected_status

            if expected_status == 200:
                data = response.json()
                assert len(data["all_test_results"]) == num_results

    @pytest.mark.parametrize(
        "user_id",
        [
            "user_123",
            "user@example.com",
            "user-with-dash",
            "user_with_underscore",
            "123456",
            "user.with.dots",
        ],
    )
    @pytest.mark.asyncio
    async def test_get_statistics_various_user_id_formats(
        self, user_id, async_client, settings
    ):
        """Параметризованный тест различных форматов user_id"""
        with (
            patch("backend.app.api.routes.TestResultRepository") as mock_repo_class,
            patch("backend.app.api.routes.UserProgressCalculator") as mock_calc,
        ):
            mock_repo = AsyncMock()
            mock_result = MagicMock()
            mock_result.id = "result_1"

            mock_repo.get_by_user_id.return_value = [mock_result]
            mock_repo.get_last_result_by_user_id.return_value = mock_result
            mock_repo.get_user_best_performance.return_value = mock_result
            mock_repo.get_user_test_result_statistics.return_value = {}
            mock_repo_class.return_value = mock_repo

            mock_calc.calculate_progress.return_value = {}

            response = await async_client.get(f"/api/statistics/{user_id}")

            assert response.status_code == 200
            data = response.json()
            assert "all_test_results" in data

    @pytest.mark.asyncio
    async def test_get_statistics_boundary_very_many_results(
        self, async_client, settings
    ):
        """Тест граничных значений - очень много результатов"""
        with (
            patch("backend.app.api.routes.TestResultRepository") as mock_repo_class,
            patch("backend.app.api.routes.UserProgressCalculator") as mock_calc,
        ):
            mock_repo = AsyncMock()

            results = []
            for i in range(1000):
                mock_result = MagicMock()
                mock_result.id = f"result_{i}"
                mock_result.chars_per_minute = 70.0 + (i % 100)
                mock_result.accuracy = 90.0 + (i % 10)
                results.append(mock_result)

            mock_repo.get_by_user_id.return_value = results
            mock_repo.get_last_result_by_user_id.return_value = results[-1]
            mock_repo.get_user_best_performance.return_value = results[-1]
            mock_repo.get_user_test_result_statistics.return_value = {
                "avg_chars_per_minute": 85.0,
                "avg_accuracy": 95.0,
            }
            mock_repo_class.return_value = mock_repo

            mock_calc.calculate_progress.return_value = {
                "total_tests": 1000,
                "improvement_percentage": 15.0,
            }

            response = await async_client.get("/api/statistics/user_123")

            assert response.status_code == 200
            data = response.json()
            assert len(data["all_test_results"]) == 1000

    @pytest.mark.parametrize(
        "malicious_user_id",
        [
            "user'; DROP TABLE--",
            "<script>alert('xss')</script>",
            "user%00null",
            "user/../../../etc/passwd",
            "user%27 OR %271%27=%271",
        ],
    )
    @pytest.mark.asyncio
    async def test_get_statistics_security_injection_attempts(
        self, malicious_user_id, async_client, settings
    ):
        """Тест безопасности - попытки инъекций в user_id"""
        with patch("backend.app.api.routes.TestResultRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_by_user_id.return_value = []
            mock_repo_class.return_value = mock_repo

            response = await async_client.get(f"/api/statistics/{malicious_user_id}")

            assert response.status_code in [404, 400]
            data = response.json()
            assert "traceback" not in str(data).lower()
            assert "sql" not in str(data).lower()

    @pytest.mark.asyncio
    async def test_get_statistics_no_results(self, async_client, settings):
        """Тест получения статистики для пользователя без результатов"""
        with patch("backend.app.api.routes.TestResultRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_by_user_id.return_value = []
            mock_repo_class.return_value = mock_repo

            response = await async_client.get("/api/statistics/user_without_results")

            assert response.status_code == 404
            assert "detail" in response.json()
            assert "No statistics found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_statistics_database_error(self, async_client, settings):
        """Тест на ошибку базы данных при получении статистики"""
        with patch("backend.app.api.routes.TestResultRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_by_user_id.side_effect = Exception(
                "Database connection error"
            )
            mock_repo_class.return_value = mock_repo

            response = await async_client.get("/api/statistics/test_user_123")

            assert response.status_code == 500
            assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_get_statistics_response_format(self, async_client, settings):
        """Тест формата ответа при получении статистики"""
        with (
            patch("backend.app.api.routes.TestResultRepository") as mock_repo_class,
            patch("backend.app.api.routes.UserProgressCalculator") as mock_calc,
        ):
            mock_repo = AsyncMock()
            mock_result = MagicMock()
            mock_result.id = "result_1"

            mock_repo.get_by_user_id.return_value = [mock_result]
            mock_repo.get_last_result_by_user_id.return_value = mock_result
            mock_repo.get_user_best_performance.return_value = mock_result
            mock_repo.get_user_test_result_statistics.return_value = {}
            mock_repo_class.return_value = mock_repo

            mock_calc.calculate_progress.return_value = {}

            response = await async_client.get("/api/statistics/test_user_123")

            assert response.status_code == 200
            data = response.json()

            assert isinstance(data, dict)
            assert "last_result" in data
            assert "best_performance" in data
            assert "avg_statistics" in data
            assert "progress_metrics" in data
            assert "all_test_results" in data

    @pytest.mark.asyncio
    async def test_get_statistics_progress_calculation_error(
        self, async_client, settings
    ):
        """Тест на ошибку при расчете прогресса"""
        with (
            patch("backend.app.api.routes.TestResultRepository") as mock_repo_class,
            patch("backend.app.api.routes.UserProgressCalculator") as mock_calc,
        ):
            mock_repo = AsyncMock()
            mock_result = MagicMock()
            mock_result.id = "result_1"

            mock_repo.get_by_user_id.return_value = [mock_result]
            mock_repo.get_last_result_by_user_id.return_value = mock_result
            mock_repo.get_user_best_performance.return_value = mock_result
            mock_repo.get_user_test_result_statistics.return_value = {}
            mock_repo_class.return_value = mock_repo

            mock_calc.calculate_progress.side_effect = Exception(
                "Progress calculation error"
            )

            response = await async_client.get("/api/statistics/test_user_123")

            assert response.status_code == 500
            assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_get_statistics_with_numeric_user_id(self, async_client, settings):
        """Тест получения статистики с числовым user_id"""
        with (
            patch("backend.app.api.routes.TestResultRepository") as mock_repo_class,
            patch("backend.app.api.routes.UserProgressCalculator") as mock_calc,
        ):
            mock_repo = AsyncMock()
            mock_result = MagicMock()
            mock_result.id = "result_1"

            mock_repo.get_by_user_id.return_value = [mock_result]
            mock_repo.get_last_result_by_user_id.return_value = mock_result
            mock_repo.get_user_best_performance.return_value = mock_result
            mock_repo.get_user_test_result_statistics.return_value = {}
            mock_repo_class.return_value = mock_repo

            mock_calc.calculate_progress.return_value = {}

            response = await async_client.get("/api/statistics/12345")

            assert response.status_code == 200
            data = response.json()
            assert "all_test_results" in data

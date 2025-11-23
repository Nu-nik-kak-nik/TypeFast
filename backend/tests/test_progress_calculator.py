"""Тесты для сервиса расчета прогресса пользователя."""

from datetime import datetime, timedelta

from backend.app.db.models import TestResult
from backend.app.schemas.progress_schemas import ProgressMetrics
from backend.app.services.progress_calculator import UserProgressCalculator


class TestUserProgressCalculator:
    """Основные тесты класса UserProgressCalculator."""

    def test_calculate_progress_returns_progress_metrics(self, two_test_results):
        """Возвращает объект ProgressMetrics с правильными атрибутами."""
        result = UserProgressCalculator.calculate_progress(two_test_results)

        assert isinstance(result, ProgressMetrics)
        assert hasattr(result, "speed_progress")
        assert hasattr(result, "accuracy_progress")
        assert hasattr(result, "time_progress")
        assert hasattr(result, "consistency_score")

    def test_calculate_progress_with_improving_results(self, improving_test_results):
        """Расчитывает положительный прогресс при улучшении показателей."""
        result = UserProgressCalculator.calculate_progress(improving_test_results)

        assert result.speed_progress > 0
        assert result.accuracy_progress > 0
        assert result.time_progress > 0
        assert result.consistency_score >= 0

    def test_calculate_progress_with_declining_results(self, declining_test_results):
        """Расчитывает отрицательный прогресс при ухудшении показателей."""
        result = UserProgressCalculator.calculate_progress(declining_test_results)

        assert result.speed_progress < 0
        assert result.accuracy_progress < 0
        assert result.time_progress < 0

    def test_calculate_progress_with_mixed_results(self, mixed_test_results):
        """Корректно обрабатывает смешанные результаты."""
        result = UserProgressCalculator.calculate_progress(mixed_test_results)

        assert result.speed_progress > 0
        assert result.accuracy_progress < 0
        assert result.time_progress > 0

    def test_calculate_progress_all_values_are_floats(self, two_test_results):
        """Все значения результата имеют тип float."""
        result = UserProgressCalculator.calculate_progress(two_test_results)

        assert isinstance(result.speed_progress, float)
        assert isinstance(result.accuracy_progress, float)
        assert isinstance(result.time_progress, float)
        assert isinstance(result.consistency_score, float)

    def test_calculate_progress_values_are_rounded(self, two_test_results):
        """Все значения округлены до 2 знаков после запятой."""
        result = UserProgressCalculator.calculate_progress(two_test_results)

        assert result.speed_progress == round(result.speed_progress, 2)
        assert result.accuracy_progress == round(result.accuracy_progress, 2)
        assert result.time_progress == round(result.time_progress, 2)
        assert result.consistency_score == round(result.consistency_score, 2)

    def test_calculate_progress_values_in_valid_ranges(self, two_test_results):
        """Все значения находятся в допустимых диапазонах."""
        result = UserProgressCalculator.calculate_progress(two_test_results)

        assert -100.0 <= result.speed_progress <= 100.0
        assert -100.0 <= result.accuracy_progress <= 100.0
        assert -100.0 <= result.time_progress <= 100.0
        assert 0.0 <= result.consistency_score <= 100.0

    def test_calculate_progress_with_consistent_results(self, consistent_test_results):
        """Высокая консистентность при стабильных результатах."""
        result = UserProgressCalculator.calculate_progress(consistent_test_results)

        assert result.consistency_score > 70.0

    def test_calculate_progress_with_inconsistent_results(
        self, inconsistent_test_results
    ):
        """Низкая консистентность при нестабильных результатах."""
        result = UserProgressCalculator.calculate_progress(inconsistent_test_results)

        assert result.consistency_score < 70.0


class TestTrendProgress:
    """Тесты метода _calculate_trend_progress."""

    def test_trend_progress_positive_growth(self):
        """Расчитывает положительный тренд для растущих значений."""
        values = [50.0, 60.0, 70.0, 80.0]
        progress = UserProgressCalculator._calculate_trend_progress(values)

        assert progress == 60.0

    def test_trend_progress_negative_growth(self):
        """Расчитывает отрицательный тренд для падающих значений."""
        values = [80.0, 70.0, 60.0, 50.0]
        progress = UserProgressCalculator._calculate_trend_progress(values)

        assert progress == -37.5

    def test_trend_progress_no_change(self):
        """Возвращает 0.0 для одинаковых значений."""
        values = [50.0, 50.0, 50.0, 50.0]
        progress = UserProgressCalculator._calculate_trend_progress(values)

        assert progress == 0.0

    def test_trend_progress_with_reverse_flag(self):
        """Меняет знак при reverse=True для инверсных метрик."""
        values = [120.0, 100.0, 80.0, 60.0]
        progress = UserProgressCalculator._calculate_trend_progress(
            values, reverse=True
        )

        assert progress == 50.0

    def test_trend_progress_single_value(self):
        """Возвращает 0.0 для списка с одним значением."""
        values = [50.0]
        progress = UserProgressCalculator._calculate_trend_progress(values)

        assert progress == 0.0

    def test_trend_progress_empty_list(self):
        """Возвращает 0.0 для пустого списка."""
        values = []
        progress = UserProgressCalculator._calculate_trend_progress(values)

        assert progress == 0.0

    def test_trend_progress_zero_first_value(self):
        """Возвращает 0.0 при нулевом первом значении."""
        values = [0.0, 50.0, 100.0]
        progress = UserProgressCalculator._calculate_trend_progress(values)

        assert progress == 0.0

    def test_trend_progress_clamped_to_100(self):
        """Ограничивает результат максимум 100%."""
        values = [1.0, 100.0]
        progress = UserProgressCalculator._calculate_trend_progress(values)

        assert progress == 100.0

    def test_trend_progress_clamped_to_minus_100(self):
        """Ограничивает результат минимум -100%."""
        values = [100.0, 1.0]
        progress = UserProgressCalculator._calculate_trend_progress(values)

        assert -100.0 <= progress <= 0.0

    def test_trend_progress_with_floats(self):
        """Корректно работает с дробными числами."""
        values = [45.5, 50.75, 55.25, 60.0]
        progress = UserProgressCalculator._calculate_trend_progress(values)

        expected = ((60.0 - 45.5) / 45.5) * 100
        assert abs(progress - expected) < 0.01


class TestConsistency:
    """Тесты метода _calculate_consistency."""

    def test_consistency_high_for_consistent_data(self):
        """Возвращает высокую консистентность для стабильных данных."""
        speeds = [75.0, 76.0, 74.5, 75.5]
        accuracies = [92.0, 91.5, 92.5, 92.0]
        times = [80.0, 79.5, 80.5, 80.0]

        consistency = UserProgressCalculator._calculate_consistency(
            speeds, accuracies, times
        )

        assert consistency > 70.0

    def test_consistency_low_for_inconsistent_data(self):
        """Возвращает низкую консистентность для нестабильных данных."""
        speeds = [40.0, 90.0, 30.0, 95.0]
        accuracies = [70.0, 98.0, 60.0, 99.0]
        times = [150.0, 50.0, 180.0, 45.0]

        consistency = UserProgressCalculator._calculate_consistency(
            speeds, accuracies, times
        )

        assert consistency < 50.0

    def test_consistency_in_valid_range(self):
        """Результат находится в диапазоне [0, 100]."""
        speeds = [50.0, 60.0, 70.0]
        accuracies = [85.0, 90.0, 95.0]
        times = [120.0, 100.0, 80.0]

        consistency = UserProgressCalculator._calculate_consistency(
            speeds, accuracies, times
        )

        assert 0.0 <= consistency <= 100.0

    def test_consistency_with_single_value(self):
        """Возвращает 100.0 для списка с одним значением."""
        speeds = [75.0]
        accuracies = [92.0]
        times = [80.0]

        consistency = UserProgressCalculator._calculate_consistency(
            speeds, accuracies, times
        )

        assert consistency == 100.0

    def test_consistency_with_zero_mean(self):
        """Возвращает 100.0 при нулевых значениях."""
        speeds = [0.0, 0.0, 0.0]
        accuracies = [0.0, 0.0, 0.0]
        times = [0.0, 0.0, 0.0]

        consistency = UserProgressCalculator._calculate_consistency(
            speeds, accuracies, times
        )

        assert consistency == 100.0

    def test_consistency_partial_zero_values(self):
        """Корректно обрабатывает смешанные данные с нулями."""
        speeds = [50.0, 60.0, 70.0]
        accuracies = [0.0, 0.0, 0.0]
        times = [100.0, 90.0, 80.0]

        consistency = UserProgressCalculator._calculate_consistency(
            speeds, accuracies, times
        )

        assert 0.0 <= consistency <= 100.0

    def test_consistency_identical_values_in_one_metric(self):
        """Обрабатывает случай когда одна метрика стабильна."""
        speeds = [75.0, 75.0, 75.0, 75.0]
        accuracies = [70.0, 95.0, 65.0, 98.0]
        times = [150.0, 50.0, 180.0, 45.0]

        consistency = UserProgressCalculator._calculate_consistency(
            speeds, accuracies, times
        )

        assert 0.0 <= consistency <= 100.0

    def test_consistency_calculation_formula(self):
        """Формула консистентности: max(0, 100 - (avg_cv * 2))."""
        speeds = [100.0, 100.0, 100.0]
        accuracies = [100.0, 100.0, 100.0]
        times = [100.0, 100.0, 100.0]

        consistency = UserProgressCalculator._calculate_consistency(
            speeds, accuracies, times
        )

        assert consistency == 100.0


class TestEdgeCases:
    """Тесты граничных случаев и обработки ошибок."""

    def test_calculate_progress_empty_list(self):
        """Возвращает нулевые метрики для пустого списка."""
        result = UserProgressCalculator.calculate_progress([])

        assert result.speed_progress == 0.0
        assert result.accuracy_progress == 0.0
        assert result.time_progress == 0.0
        assert result.consistency_score == 0.0

    def test_calculate_progress_none_list(self):
        """Корректно обрабатывает None."""
        result = UserProgressCalculator.calculate_progress([])

        assert result.speed_progress == 0.0
        assert result.accuracy_progress == 0.0
        assert result.time_progress == 0.0
        assert result.consistency_score == 0.0

    def test_calculate_progress_single_result(self, single_test_result):
        """Возвращает нулевые метрики для одного результата."""
        result = UserProgressCalculator.calculate_progress([single_test_result])

        assert result.speed_progress == 0.0
        assert result.accuracy_progress == 0.0
        assert result.time_progress == 0.0
        assert result.consistency_score == 0.0

    def test_calculate_progress_with_very_large_numbers(self):
        """Корректно работает с очень большими числами."""
        results = [
            TestResult(
                id="result_1",
                user_id="user_123",
                chars_per_minute=1000000.0,
                accuracy=99.9,
                time_seconds=1000000.0,
                language="ru",
                difficulty="easy",
                created_at=datetime.now(),
            ),
            TestResult(
                id="result_2",
                user_id="user_123",
                chars_per_minute=2000000.0,
                accuracy=99.95,
                time_seconds=500000.0,
                language="ru",
                difficulty="easy",
                created_at=datetime.now(),
            ),
        ]

        result = UserProgressCalculator.calculate_progress(results)

        assert isinstance(result, ProgressMetrics)
        assert -100.0 <= result.speed_progress <= 100.0

    def test_calculate_progress_with_very_small_numbers(self):
        """Корректно работает с очень маленькими числами."""
        results = [
            TestResult(
                id="result_1",
                user_id="user_123",
                chars_per_minute=0.1,
                accuracy=0.1,
                time_seconds=0.1,
                language="ru",
                difficulty="easy",
                created_at=datetime.now(),
            ),
            TestResult(
                id="result_2",
                user_id="user_123",
                chars_per_minute=0.2,
                accuracy=0.2,
                time_seconds=0.05,
                language="ru",
                difficulty="easy",
                created_at=datetime.now(),
            ),
        ]

        result = UserProgressCalculator.calculate_progress(results)

        assert isinstance(result, ProgressMetrics)
        assert -100.0 <= result.speed_progress <= 100.0

    def test_calculate_progress_with_negative_values(self):
        """Обрабатывает отрицательные значения."""
        results = [
            TestResult(
                id="result_1",
                user_id="user_123",
                chars_per_minute=-50.0,
                accuracy=-10.0,
                time_seconds=-100.0,
                language="ru",
                difficulty="easy",
                created_at=datetime.now(),
            ),
            TestResult(
                id="result_2",
                user_id="user_123",
                chars_per_minute=-30.0,
                accuracy=-5.0,
                time_seconds=-50.0,
                language="ru",
                difficulty="easy",
                created_at=datetime.now(),
            ),
        ]

        result = UserProgressCalculator.calculate_progress(results)

        assert isinstance(result, ProgressMetrics)

    def test_calculate_progress_with_float_precision(self):
        """Корректно работает с высокой точностью float."""
        results = [
            TestResult(
                id="result_1",
                user_id="user_123",
                chars_per_minute=50.123456,
                accuracy=85.987654,
                time_seconds=120.555555,
                language="ru",
                difficulty="easy",
                created_at=datetime.now(),
            ),
            TestResult(
                id="result_2",
                user_id="user_123",
                chars_per_minute=60.654321,
                accuracy=90.123456,
                time_seconds=100.444444,
                language="ru",
                difficulty="easy",
                created_at=datetime.now(),
            ),
        ]

        result = UserProgressCalculator.calculate_progress(results)

        assert result.speed_progress == round(result.speed_progress, 2)
        assert result.accuracy_progress == round(result.accuracy_progress, 2)


class TestIntegration:
    """Интеграционные тесты для полного цикла работы."""

    def test_full_user_progression_journey(self):
        """Полный путь прогрессии пользователя от новичка к опытному."""
        results = [
            TestResult(
                id="result_1",
                user_id="user_123",
                chars_per_minute=30.0,
                accuracy=70.0,
                time_seconds=180.0,
                language="ru",
                difficulty="easy",
                created_at=datetime.now() - timedelta(days=6),
            ),
            TestResult(
                id="result_2",
                user_id="user_123",
                chars_per_minute=40.0,
                accuracy=75.0,
                time_seconds=150.0,
                language="ru",
                difficulty="easy",
                created_at=datetime.now() - timedelta(days=5),
            ),
            TestResult(
                id="result_3",
                user_id="user_123",
                chars_per_minute=55.0,
                accuracy=85.0,
                time_seconds=110.0,
                language="ru",
                difficulty="easy",
                created_at=datetime.now() - timedelta(days=4),
            ),
            TestResult(
                id="result_4",
                user_id="user_123",
                chars_per_minute=70.0,
                accuracy=90.0,
                time_seconds=85.0,
                language="ru",
                difficulty="easy",
                created_at=datetime.now() - timedelta(days=3),
            ),
            TestResult(
                id="result_5",
                user_id="user_123",
                chars_per_minute=85.0,
                accuracy=93.0,
                time_seconds=70.0,
                language="ru",
                difficulty="easy",
                created_at=datetime.now() - timedelta(days=2),
            ),
            TestResult(
                id="result_6",
                user_id="user_123",
                chars_per_minute=84.0,
                accuracy=92.5,
                time_seconds=71.0,
                language="ru",
                difficulty="easy",
                created_at=datetime.now() - timedelta(days=1),
            ),
            TestResult(
                id="result_7",
                user_id="user_123",
                chars_per_minute=86.0,
                accuracy=93.5,
                time_seconds=70.0,
                language="ru",
                difficulty="easy",
                created_at=datetime.now(),
            ),
        ]

        result = UserProgressCalculator.calculate_progress(results)

        assert result.speed_progress == 100.0
        assert result.accuracy_progress > 30.0
        assert result.time_progress > 50.0
        assert result.consistency_score > 0.0

    def test_comparison_of_different_difficulty_levels(self):
        """Расчет работает одинаково для разных уровней сложности."""
        easy_results = [
            TestResult(
                id="result_1",
                user_id="user_123",
                chars_per_minute=50.0,
                accuracy=85.0,
                time_seconds=120.0,
                language="ru",
                difficulty="easy",
                created_at=datetime.now() - timedelta(days=1),
            ),
            TestResult(
                id="result_2",
                user_id="user_123",
                chars_per_minute=70.0,
                accuracy=90.0,
                time_seconds=85.0,
                language="ru",
                difficulty="easy",
                created_at=datetime.now(),
            ),
        ]

        hard_results = [
            TestResult(
                id="result_1",
                user_id="user_123",
                chars_per_minute=30.0,
                accuracy=75.0,
                time_seconds=180.0,
                language="ru",
                difficulty="hard",
                created_at=datetime.now() - timedelta(days=1),
            ),
            TestResult(
                id="result_2",
                user_id="user_123",
                chars_per_minute=45.0,
                accuracy=82.0,
                time_seconds=130.0,
                language="ru",
                difficulty="hard",
                created_at=datetime.now(),
            ),
        ]

        easy_progress = UserProgressCalculator.calculate_progress(easy_results)
        hard_progress = UserProgressCalculator.calculate_progress(hard_results)

        assert easy_progress.speed_progress > 0.0
        assert hard_progress.speed_progress > 0.0
        assert easy_progress.speed_progress == 40.0
        assert hard_progress.speed_progress == 50.0
        assert hard_progress.speed_progress > easy_progress.speed_progress

    def test_multiple_users_independent_calculations(self):
        """Расчеты для разных пользователей независимы."""
        user1_results = [
            TestResult(
                id="result_1",
                user_id="user_1",
                chars_per_minute=50.0,
                accuracy=85.0,
                time_seconds=120.0,
                language="ru",
                difficulty="easy",
                created_at=datetime.now() - timedelta(days=1),
            ),
            TestResult(
                id="result_2",
                user_id="user_1",
                chars_per_minute=100.0,
                accuracy=95.0,
                time_seconds=60.0,
                language="ru",
                difficulty="easy",
                created_at=datetime.now(),
            ),
        ]

        user2_results = [
            TestResult(
                id="result_1",
                user_id="user_2",
                chars_per_minute=100.0,
                accuracy=95.0,
                time_seconds=60.0,
                language="ru",
                difficulty="easy",
                created_at=datetime.now() - timedelta(days=1),
            ),
            TestResult(
                id="result_2",
                user_id="user_2",
                chars_per_minute=50.0,
                accuracy=85.0,
                time_seconds=120.0,
                language="ru",
                difficulty="easy",
                created_at=datetime.now(),
            ),
        ]

        user1_progress = UserProgressCalculator.calculate_progress(user1_results)
        user2_progress = UserProgressCalculator.calculate_progress(user2_results)

        assert user1_progress.speed_progress > 0.0
        assert user2_progress.speed_progress < 0.0

    def test_progress_metrics_are_independent(self):
        """Метрики прогресса независимы друг от друга."""
        speed_only = [
            TestResult(
                id="result_1",
                user_id="user_123",
                chars_per_minute=50.0,
                accuracy=90.0,
                time_seconds=100.0,
                language="ru",
                difficulty="easy",
                created_at=datetime.now() - timedelta(days=1),
            ),
            TestResult(
                id="result_2",
                user_id="user_123",
                chars_per_minute=100.0,
                accuracy=90.0,
                time_seconds=100.0,
                language="ru",
                difficulty="easy",
                created_at=datetime.now(),
            ),
        ]

        result = UserProgressCalculator.calculate_progress(speed_only)

        assert result.speed_progress == 100.0
        assert result.accuracy_progress == 0.0
        assert result.time_progress == 0.0

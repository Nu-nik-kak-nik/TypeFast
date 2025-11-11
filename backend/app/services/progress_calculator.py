from statistics import mean, pstdev

from backend.app.db.models import TestResult
from backend.app.schemas.progress_schemas import ProgressMetrics


class UserProgressCalculator:
    @staticmethod
    def calculate_progress(
        all_test_results: list[TestResult],
    ) -> ProgressMetrics:
        """Расчет метрик прогресса пользователя"""
        if not all_test_results or len(all_test_results) < 2:
            return ProgressMetrics(
                speed_progress=0.0,
                accuracy_progress=0.0,
                time_progress=0.0,
                consistency_score=0.0,
            )

        speeds = [float(result.chars_per_minute) for result in all_test_results]
        accuracies = [float(result.accuracy) for result in all_test_results]
        times = [float(result.time_seconds) for result in all_test_results]

        speed_progress = UserProgressCalculator._calculate_trend_progress(speeds)
        accuracy_progress = UserProgressCalculator._calculate_trend_progress(accuracies)
        time_progress = UserProgressCalculator._calculate_trend_progress(
            times, reverse=True
        )

        consistency_score = UserProgressCalculator._calculate_consistency(
            speeds, accuracies, times
        )

        return ProgressMetrics(
            speed_progress=round(speed_progress, 2),
            accuracy_progress=round(accuracy_progress, 2),
            time_progress=round(time_progress, 2),
            consistency_score=round(consistency_score, 2),
        )

    @staticmethod
    def _calculate_trend_progress(values: list[float], reverse: bool = False) -> float:
        """Расчет тренда прогресса по значениям"""
        if len(values) < 2:
            return 0.0

        first_value = values[0]
        last_value = values[-1]

        if first_value == 0:
            return 0.0

        progress_percent = ((last_value - first_value) / first_value) * 100

        if reverse:
            progress_percent = -progress_percent

        return max(-100.0, min(100.0, progress_percent))

    @staticmethod
    def _calculate_consistency(
        speeds: list[float], accuracies: list[float], times: list[float]
    ) -> float:
        """Расчет оценки консистентности (стабильности) результатов"""

        def coefficient_of_variation(values: list[float]) -> float:
            """Коэффициент вариации (мера разброса данных)"""
            if not values or mean(values) == 0:
                return 0.0

            try:
                std = pstdev(values) if len(values) > 1 else 0
                return (std / mean(values)) * 100
            except Exception:
                return 0.0

        cv_speed = coefficient_of_variation(speeds)
        cv_accuracy = coefficient_of_variation(accuracies)
        cv_time = coefficient_of_variation(times)

        avg_cv = mean([cv_speed, cv_accuracy, cv_time])
        consistency = max(0.0, 100.0 - (avg_cv * 2))

        return min(100.0, consistency)

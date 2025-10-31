from statistics import mean, pstdev
from backend.app.schemas.progress_schemas import ProgressMetrics
from backend.app.db.models import TestResult


class UserProgressCalculator:
    @staticmethod
    async def calculate_progress(
        all_test_results: list[TestResult],
    ) -> ProgressMetrics:
        if not all_test_results or len(all_test_results) < 2:
            return ProgressMetrics(
                speed_progress=0.0, accuracy_progress=0.0, time_progress=0.0
            )

        speeds = [float(result.chars_per_minute) for result in all_test_results]
        accuracies = [float(result.accuracy) for result in all_test_results]
        times = [float(result.time_seconds) for result in all_test_results]

        speed_progress = UserProgressCalculator._calculate_single_progress(speeds)
        accuracy_progress = UserProgressCalculator._calculate_single_progress(
            accuracies
        )
        time_progress = UserProgressCalculator._calculate_single_progress(
            times, reverse=True
        )

        return ProgressMetrics(
            speed_progress=round(speed_progress, 3) * 100,
            accuracy_progress=round(accuracy_progress, 3) * 100,
            time_progress=round(time_progress, 3) * 100,
        )

    @staticmethod
    def _calculate_single_progress(values: list[float], reverse: bool = False) -> float:
        if len(values) < 2:
            return 0.0

        avg = mean(values)
        std_dev = pstdev(values)

        if std_dev == 0:
            return 0.0

        last_value = values[-1]
        progress = ((last_value - avg) / std_dev) * (1 if not reverse else -1)

        return progress

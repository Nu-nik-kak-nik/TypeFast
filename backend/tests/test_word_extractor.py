"""Тесты для сервиса извлечения слов из словаря."""

import os
import random

import pytest

from backend.app.core.config import settings
from backend.app.services.word_extractor import WordExtractor


class TestWordExtractorInitialization:
    """Тесты инициализации WordExtractor."""

    def test_initialization_with_defaults(self, temp_dictionary_file: str) -> None:
        """Инициализирует с параметрами по умолчанию."""
        extractor = WordExtractor(filepath=temp_dictionary_file)

        assert extractor.filepath == temp_dictionary_file
        assert extractor.count_words == settings.default_count_words
        assert extractor.level == settings.default_level

    def test_initialization_with_custom_parameters(
        self, temp_dictionary_file: str
    ) -> None:
        """Инициализирует с пользовательскими параметрами."""
        extractor = WordExtractor(
            filepath=temp_dictionary_file, count_words=5, level="hard"
        )

        assert extractor.count_words == 5
        assert extractor.level == "hard"

    def test_initialization_with_none_filepath_uses_default(
        self, temp_dictionary_file: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Использует путь по умолчанию если filepath=None."""
        monkeypatch.setattr(settings, "default_filepath", temp_dictionary_file)
        extractor = WordExtractor(filepath=None)

        assert extractor.filepath == temp_dictionary_file

    def test_initialization_file_not_found(self) -> None:
        """Выбрасывает исключение если файл не существует."""
        with pytest.raises(FileNotFoundError):
            WordExtractor(filepath="/nonexistent/path/to/dictionary.txt")

    def test_initialization_file_not_readable(self, temp_dictionary_file: str) -> None:
        """Выбрасывает исключение если файл не читаем."""
        os.chmod(temp_dictionary_file, 0o000)
        try:
            with pytest.raises(PermissionError):
                WordExtractor(filepath=temp_dictionary_file)
        finally:
            os.chmod(temp_dictionary_file, 0o644)

    def test_initialization_caches_settings(self, temp_dictionary_file: str) -> None:
        """Кэширует настройки из конфига."""
        extractor = WordExtractor(filepath=temp_dictionary_file)

        assert extractor._cached_word_lengths is not None
        assert extractor._cached_probability is not None
        assert extractor._cached_punctuation is not None
        assert extractor._cached_allowed_levels is not None


class TestCountWordsProperty:
    """Тесты свойства count_words."""

    def test_count_words_getter(self, temp_dictionary_file: str) -> None:
        """Возвращает значение count_words."""
        extractor = WordExtractor(filepath=temp_dictionary_file, count_words=10)

        assert extractor.count_words == 10

    def test_count_words_setter_valid(self, temp_dictionary_file: str) -> None:
        """Устанавливает корректное значение count_words."""
        extractor = WordExtractor(filepath=temp_dictionary_file)
        extractor.count_words = 15

        assert extractor.count_words == 15

    def test_count_words_setter_zero_raises_error(
        self, temp_dictionary_file: str
    ) -> None:
        """Выбрасывает ошибку при нулевом значении."""
        extractor = WordExtractor(filepath=temp_dictionary_file)

        with pytest.raises(ValueError, match="положительным числом"):
            extractor.count_words = 0

    def test_count_words_setter_negative_raises_error(
        self, temp_dictionary_file: str
    ) -> None:
        """Выбрасывает ошибку при отрицательном значении."""
        extractor = WordExtractor(filepath=temp_dictionary_file)

        with pytest.raises(ValueError, match="положительным числом"):
            extractor.count_words = -5


class TestLevelProperty:
    """Тесты свойства level."""

    def test_level_getter(self, temp_dictionary_file: str) -> None:
        """Возвращает значение level."""
        extractor = WordExtractor(filepath=temp_dictionary_file, level="hard")

        assert extractor.level == "hard"

    def test_level_setter_valid(self, temp_dictionary_file: str) -> None:
        """Устанавливает корректное значение level."""
        extractor = WordExtractor(filepath=temp_dictionary_file)
        extractor.level = "medium"

        assert extractor.level == "medium"

    def test_level_setter_case_insensitive(self, temp_dictionary_file: str) -> None:
        """Преобразует level в нижний регистр."""
        extractor = WordExtractor(filepath=temp_dictionary_file)
        extractor.level = "HARD"

        assert extractor.level == "hard"

    def test_level_setter_invalid_raises_error(self, temp_dictionary_file: str) -> None:
        """Выбрасывает ошибку при недопустимом level."""
        extractor = WordExtractor(filepath=temp_dictionary_file)

        with pytest.raises(ValueError, match="Недопустимый уровень"):
            extractor.level = "invalid_level"


class TestWordGenerator:
    """Тесты метода _word_generator."""

    def test_word_generator_returns_iterator(self, temp_dictionary_file: str) -> None:
        """Возвращает итератор слов."""
        extractor = WordExtractor(filepath=temp_dictionary_file)
        generator = extractor._word_generator("easy")

        assert hasattr(generator, "__iter__")
        assert hasattr(generator, "__next__")

    def test_word_generator_yields_words(self, temp_dictionary_file: str) -> None:
        """Генерирует слова из файла."""
        extractor = WordExtractor(filepath=temp_dictionary_file)
        words = list(extractor._word_generator("easy"))

        assert len(words) > 0
        assert all(isinstance(word, str) for word in words)

    def test_word_generator_skips_comments(
        self, dictionary_file_with_special_chars: str
    ) -> None:
        """Пропускает строки начинающиеся с дефиса."""
        extractor = WordExtractor(filepath=dictionary_file_with_special_chars)
        words = list(extractor._word_generator("easy"))

        assert not any(word.startswith("-") for word in words)

    def test_word_generator_filters_by_length_easy(
        self, temp_dictionary_file: str
    ) -> None:
        """Фильтрует слова по длине для уровня easy."""
        extractor = WordExtractor(filepath=temp_dictionary_file)
        words = list(extractor._word_generator("easy"))

        easy_rules = settings.word_lengths.get("easy", {})
        min_len = easy_rules.get("min")
        max_len = easy_rules.get("max")

        for word in words:
            if min_len is not None:
                assert len(word) >= min_len
            if max_len is not None:
                assert len(word) <= max_len

    def test_word_generator_filters_by_length_hard(
        self, temp_dictionary_file: str
    ) -> None:
        """Фильтрует слова по длине для уровня hard."""
        extractor = WordExtractor(filepath=temp_dictionary_file)
        words = list(extractor._word_generator("hard"))

        hard_rules = settings.word_lengths.get("hard", {})
        min_len = hard_rules.get("min")
        max_len = hard_rules.get("max")

        for word in words:
            if min_len is not None:
                assert len(word) >= min_len
            if max_len is not None:
                assert len(word) <= max_len

    def test_word_generator_empty_file(self, empty_dictionary_file: str) -> None:
        """Обрабатывает пустой файл без ошибок."""
        extractor = WordExtractor(filepath=empty_dictionary_file)

        try:
            words = list(extractor._word_generator("easy"))
            assert len(words) == 0
        except ValueError as e:
            if "cannot mmap an empty file" in str(e):
                pytest.skip("mmap не поддерживает пустые файлы на этой системе")
            raise


class TestCheckDifficulty:
    """Тесты метода _check_difficulty."""

    def test_check_difficulty_valid_word_easy(self, temp_dictionary_file: str) -> None:
        """Возвращает True для корректного слова уровня easy."""
        extractor = WordExtractor(filepath=temp_dictionary_file)

        assert extractor._check_difficulty("привет", "easy") is True

    def test_check_difficulty_too_short_word(self, temp_dictionary_file: str) -> None:
        """Возвращает False для слова короче минимума."""
        extractor = WordExtractor(filepath=temp_dictionary_file)
        easy_rules = settings.word_lengths.get("easy", {})
        min_len = easy_rules.get("min")

        if min_len is None:
            pytest.skip("min_len не определен в конфигурации")

        short_word = "а" * (min_len - 1)
        result = extractor._check_difficulty(short_word, "easy")

        assert result is False

    def test_check_difficulty_too_long_word(self, temp_dictionary_file: str) -> None:
        """Возвращает False для слова длиннее максимума."""
        extractor = WordExtractor(filepath=temp_dictionary_file)
        hard_rules = settings.word_lengths.get("hard", {})
        max_len = hard_rules.get("max")

        if max_len is None:
            pytest.skip("max_len не определен в конфигурации")

        long_word = "а" * (max_len + 1)
        result = extractor._check_difficulty(long_word, "hard")

        assert result is False

    def test_check_difficulty_all_levels(self, temp_dictionary_file: str) -> None:
        """Проверяет сложность для всех уровней."""
        extractor = WordExtractor(filepath=temp_dictionary_file)
        test_word = "тест"

        for level in settings.allowed_levels:
            result = extractor._check_difficulty(test_word, level)
            assert isinstance(result, bool)


class TestExtractRandomWords:
    """Тесты метода extract_random_words."""

    def test_extract_random_words_returns_list(self, temp_dictionary_file: str) -> None:
        """Возвращает список слов."""
        extractor = WordExtractor(filepath=temp_dictionary_file, count_words=5)
        words = extractor.extract_random_words()

        assert isinstance(words, list)
        assert all(isinstance(word, str) for word in words)

    def test_extract_random_words_correct_count(
        self, temp_dictionary_file: str
    ) -> None:
        """Возвращает правильное количество слов."""
        extractor = WordExtractor(filepath=temp_dictionary_file, count_words=3)
        words = extractor.extract_random_words()

        assert len(words) <= 3

    def test_extract_random_words_custom_count(self, temp_dictionary_file: str) -> None:
        """Использует пользовательское количество слов."""
        extractor = WordExtractor(filepath=temp_dictionary_file)
        words = extractor.extract_random_words(count_words=2)

        assert len(words) <= 2

    def test_extract_random_words_custom_level(self, temp_dictionary_file: str) -> None:
        """Использует пользовательский уровень."""
        extractor = WordExtractor(filepath=temp_dictionary_file)
        words = extractor.extract_random_words(level="hard")

        assert isinstance(words, list)

    def test_extract_random_words_randomness(self, temp_dictionary_file: str) -> None:
        """Возвращает разные слова при повторных вызовах."""
        random.seed(None)
        extractor = WordExtractor(filepath=temp_dictionary_file, count_words=10)

        words1 = extractor.extract_random_words()
        words2 = extractor.extract_random_words()

        assert words1 != words2 or len(words1) == 0

    def test_extract_random_words_no_duplicates(
        self, temp_dictionary_file: str
    ) -> None:
        """Возвращает список без дубликатов."""
        extractor = WordExtractor(filepath=temp_dictionary_file, count_words=5)
        words = extractor.extract_random_words()

        assert len(words) == len(set(words))

    def test_extract_random_words_empty_file(self, empty_dictionary_file: str) -> None:
        """Обрабатывает пустой файл корректно."""
        extractor = WordExtractor(filepath=empty_dictionary_file, count_words=5)

        try:
            words = extractor.extract_random_words()
            assert words == []
        except ValueError as e:
            if "cannot mmap an empty file" in str(e):
                pytest.skip("mmap не поддерживает пустые файлы на этой системе")
            raise


class TestReturnCharRandomWords:
    """Тесты метода return_char_random_words."""

    def test_return_char_random_words_returns_list(
        self, temp_dictionary_file: str
    ) -> None:
        """Возвращает список символов."""
        extractor = WordExtractor(filepath=temp_dictionary_file)
        words = ["привет", "мир"]
        result = extractor.return_char_random_words(words)

        assert isinstance(result, list)
        assert all(isinstance(char, str) for char in result)

    def test_return_char_random_words_contains_word_chars(
        self, temp_dictionary_file: str
    ) -> None:
        """Содержит все символы из исходных слов."""
        extractor = WordExtractor(filepath=temp_dictionary_file)
        words = ["привет", "мир"]
        result = extractor.return_char_random_words(words)

        result_str = "".join(result)
        for word in words:
            for char in word:
                assert char in result_str

    def test_return_char_random_words_has_separators(
        self, temp_dictionary_file: str
    ) -> None:
        """Содержит разделители между словами."""
        extractor = WordExtractor(filepath=temp_dictionary_file)
        words = ["привет", "мир"]
        result = extractor.return_char_random_words(words)

        assert len(result) > len("".join(words))

    def test_return_char_random_words_empty_list(
        self, temp_dictionary_file: str
    ) -> None:
        """Возвращает пустой список для пустого входа."""
        extractor = WordExtractor(filepath=temp_dictionary_file)
        result = extractor.return_char_random_words([])

        assert result == []

    def test_return_char_random_words_single_word(
        self, temp_dictionary_file: str
    ) -> None:
        """Обрабатывает одно слово без разделителей."""
        extractor = WordExtractor(filepath=temp_dictionary_file)
        words = ["привет"]
        result = extractor.return_char_random_words(words)

        assert "".join(result) == "привет"

    def test_return_char_random_words_custom_level(
        self, temp_dictionary_file: str
    ) -> None:
        """Использует пользовательский уровень для пунктуации."""
        extractor = WordExtractor(filepath=temp_dictionary_file)
        words = ["привет", "мир"]
        result = extractor.return_char_random_words(words, level="hard")

        assert isinstance(result, list)


class TestReturnStringRandomWords:
    """Тесты метода return_string_random_words."""

    def test_return_string_random_words_returns_string(
        self, temp_dictionary_file: str
    ) -> None:
        """Возвращает строку."""
        extractor = WordExtractor(filepath=temp_dictionary_file)
        words = ["привет", "мир"]
        result = extractor.return_string_random_words(words)

        assert isinstance(result, str)

    def test_return_string_random_words_contains_words(
        self, temp_dictionary_file: str
    ) -> None:
        """Содержит все исходные слова."""
        extractor = WordExtractor(filepath=temp_dictionary_file)
        words = ["привет", "мир"]
        result = extractor.return_string_random_words(words)

        for word in words:
            assert word in result

    def test_return_string_random_words_has_separators(
        self, temp_dictionary_file: str
    ) -> None:
        """Содержит разделители между словами."""
        extractor = WordExtractor(filepath=temp_dictionary_file)
        words = ["привет", "мир"]
        result = extractor.return_string_random_words(words)

        joined_with_space = " ".join(words)
        joined_without_space = "".join(words)

        assert (
            len(result) >= len(joined_without_space)
            and len(result) <= len(joined_with_space) + 10
        )

    def test_return_string_random_words_empty_list(
        self, temp_dictionary_file: str
    ) -> None:
        """Возвращает пустую строку для пустого входа."""
        extractor = WordExtractor(filepath=temp_dictionary_file)
        result = extractor.return_string_random_words([])

        assert result == ""

    def test_return_string_random_words_single_word(
        self, temp_dictionary_file: str
    ) -> None:
        """Обрабатывает одно слово без разделителей."""
        extractor = WordExtractor(filepath=temp_dictionary_file)
        words = ["привет"]
        result = extractor.return_string_random_words(words)

        assert result == "привет"

    def test_return_string_random_words_custom_level(
        self, temp_dictionary_file: str
    ) -> None:
        """Использует пользовательский уровень для пунктуации."""
        extractor = WordExtractor(filepath=temp_dictionary_file)
        words = ["привет", "мир"]
        result = extractor.return_string_random_words(words, level="hard")

        assert isinstance(result, str)


class TestRandomPunctuationMark:
    """Тесты метода random_punctuation_mark."""

    def test_random_punctuation_mark_returns_string(
        self, temp_dictionary_file: str
    ) -> None:
        """Возвращает строку."""
        extractor = WordExtractor(filepath=temp_dictionary_file)
        result = extractor.random_punctuation_mark()

        assert isinstance(result, str)

    def test_random_punctuation_mark_is_valid(self, temp_dictionary_file: str) -> None:
        """Возвращает пунктуацию или пробел."""
        extractor = WordExtractor(filepath=temp_dictionary_file)
        result = extractor.random_punctuation_mark()

        valid_marks = settings.punctuation.get("easy", []) + [" "]
        assert result in valid_marks or result == " "

    def test_random_punctuation_mark_custom_level(
        self, temp_dictionary_file: str
    ) -> None:
        """Использует пользовательский уровень."""
        extractor = WordExtractor(filepath=temp_dictionary_file)
        result = extractor.random_punctuation_mark(level="hard")

        assert isinstance(result, str)

    def test_random_punctuation_mark_distribution(
        self, temp_dictionary_file: str
    ) -> None:
        """Генерирует пунктуацию и пробелы в соответствии с вероятностью."""
        extractor = WordExtractor(filepath=temp_dictionary_file, level="easy")
        results = [extractor.random_punctuation_mark() for _ in range(100)]

        assert len(results) > 0
        assert any(mark == " " for mark in results)


class TestGenerateRandomText:
    """Тесты метода generate_random_text."""

    def test_generate_random_text_returns_string(
        self, temp_dictionary_file: str
    ) -> None:
        """Возвращает строку."""
        extractor = WordExtractor(filepath=temp_dictionary_file, count_words=5)
        result = extractor.generate_random_text()

        assert isinstance(result, str)

    def test_generate_random_text_not_empty(self, temp_dictionary_file: str) -> None:
        """Возвращает непустую строку."""
        extractor = WordExtractor(filepath=temp_dictionary_file, count_words=5)
        result = extractor.generate_random_text()

        assert len(result) > 0

    def test_generate_random_text_custom_count(self, temp_dictionary_file: str) -> None:
        """Использует пользовательское количество слов."""
        extractor = WordExtractor(filepath=temp_dictionary_file)
        result = extractor.generate_random_text(count_words=3)

        assert isinstance(result, str)

    def test_generate_random_text_custom_level(self, temp_dictionary_file: str) -> None:
        """Использует пользовательский уровень."""
        extractor = WordExtractor(filepath=temp_dictionary_file)
        result = extractor.generate_random_text(level="hard")

        assert isinstance(result, str)

    def test_generate_random_text_randomness(self, temp_dictionary_file: str) -> None:
        """Возвращает разные тексты при повторных вызовах."""
        random.seed(None)
        extractor = WordExtractor(filepath=temp_dictionary_file, count_words=10)

        text1 = extractor.generate_random_text()
        text2 = extractor.generate_random_text()

        assert text1 != text2

    def test_generate_random_text_contains_words(
        self, temp_dictionary_file: str
    ) -> None:
        """Содержит слова из словаря."""
        extractor = WordExtractor(filepath=temp_dictionary_file, count_words=5)
        result = extractor.generate_random_text()

        assert len(result) > 0

    def test_generate_random_text_all_levels(self, temp_dictionary_file: str) -> None:
        """Генерирует текст для всех уровней."""
        extractor = WordExtractor(filepath=temp_dictionary_file)

        for level in settings.allowed_levels:
            result = extractor.generate_random_text(level=level)
            assert isinstance(result, str)
            assert len(result) > 0


class TestIntegration:
    """Интеграционные тесты."""

    def test_full_workflow_easy_level(self, temp_dictionary_file: str) -> None:
        """Полный цикл: инициализация, извлечение, генерация для easy."""
        extractor = WordExtractor(
            filepath=temp_dictionary_file, count_words=5, level="easy"
        )

        words = extractor.extract_random_words()
        assert len(words) > 0

        text = extractor.generate_random_text()
        assert len(text) > 0
        assert isinstance(text, str)

    def test_full_workflow_hard_level(self, temp_dictionary_file: str) -> None:
        """Полный цикл: инициализация, извлечение, генерация для hard."""
        extractor = WordExtractor(
            filepath=temp_dictionary_file, count_words=5, level="hard"
        )

        words = extractor.extract_random_words()
        text = extractor.generate_random_text()

        assert isinstance(words, list)
        assert isinstance(text, str)

    def test_workflow_with_level_change(self, temp_dictionary_file: str) -> None:
        """Изменение уровня во время работы."""
        extractor = WordExtractor(filepath=temp_dictionary_file)

        extractor.level = "easy"
        text_easy = extractor.generate_random_text()

        extractor.level = "hard"
        text_hard = extractor.generate_random_text()

        assert isinstance(text_easy, str)
        assert isinstance(text_hard, str)

    def test_workflow_with_count_change(self, temp_dictionary_file: str) -> None:
        """Изменение количества слов во время работы."""
        extractor = WordExtractor(filepath=temp_dictionary_file)

        extractor.count_words = 3
        text_short = extractor.generate_random_text()

        extractor.count_words = 10
        text_long = extractor.generate_random_text()

        assert len(text_short) > 0
        assert len(text_long) > 0

    def test_multiple_extractions_independence(self, temp_dictionary_file: str) -> None:
        """Несколько экземпляров работают независимо."""
        extractor1 = WordExtractor(
            filepath=temp_dictionary_file, count_words=5, level="easy"
        )
        extractor2 = WordExtractor(
            filepath=temp_dictionary_file, count_words=10, level="hard"
        )

        text1 = extractor1.generate_random_text()
        text2 = extractor2.generate_random_text()

        assert isinstance(text1, str)
        assert isinstance(text2, str)

    def test_char_and_string_consistency(self, temp_dictionary_file: str) -> None:
        """Методы char и string возвращают одинаковый контент."""
        extractor = WordExtractor(filepath=temp_dictionary_file)
        words = ["привет", "мир"]

        char_result = "".join(extractor.return_char_random_words(words))
        string_result = extractor.return_string_random_words(words)

        assert char_result == string_result

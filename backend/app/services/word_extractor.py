import random
import mmap
import os
from collections.abc import Iterator
from backend.app.core.config import settings


class WordExtractor:
    def __init__(
        self,
        filepath: str | None = None,
        count_words: int | None = None,
        level: str | None = None,
    ) -> None:
        """Инициализация класса по извлечению слов из словаря."""
        self._settings = settings
        self.filepath: str = filepath or str(self._settings.default_filepath)
        self._validate_file()

        self._count_words: int = count_words or self._settings.default_count_words
        self._level: str = level or self._settings.default_level

        self._cached_word_lengths = self._settings.word_lengths
        self._cached_probability = self._settings.probability
        self._cached_punctuation = self._settings.punctuation
        self._cached_allowed_levels = self._settings.allowed_levels

    @property
    def count_words(self) -> int:
        """Геттер для count_words с валидацией."""
        return self._count_words

    @count_words.setter
    def count_words(self, value: int) -> None:
        """Сеттер для count_words с проверками."""
        if value <= 0:
            raise ValueError("count_words должен быть положительным числом")
        self._count_words = value

    @property
    def level(self) -> str:
        """Геттер для level с валидацией."""
        return self._level

    @level.setter
    def level(self, value: str) -> None:
        """Сеттер для level с проверкой допустимых значений."""
        if value.lower() not in self._cached_allowed_levels:
            raise ValueError(
                f"Недопустимый уровень. Используйте: {', '.join(self._cached_allowed_levels)}"
            )
        self._level = value.lower()

    def _validate_file(self) -> None:
        """Проверка существования и доступности файла."""
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"Словарь не найден: {self.filepath}")
        if not os.access(self.filepath, os.R_OK):
            raise PermissionError(f"Нет прав на чтение файла: {self.filepath}")

    def _word_generator(self, level: str) -> Iterator[str]:
        """Генератор слов с использованием memory-mapped file."""
        length_rules = self._cached_word_lengths.get(level, {})
        min_len = length_rules.get("min")
        max_len = length_rules.get("max")

        with open(self.filepath, "rb") as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmapped_file:
                for line in iter(mmapped_file.readline, b""):
                    word = line.decode("utf-8").strip()
                    if word and not word.startswith("-"):
                        word_length = len(word)
                        if min_len is not None and word_length < min_len:
                            continue
                        if max_len is not None and word_length > max_len:
                            continue
                        yield word

    def _check_difficulty(self, word: str, level: str) -> bool:
        """Проверка сложности слова (оптимизированная версия)."""
        word_length = len(word)
        length_rules = self._cached_word_lengths.get(level, {})
        min_len = length_rules.get("min")
        max_len = length_rules.get("max")

        if min_len is not None and word_length < min_len:
            return False
        if max_len is not None and word_length > max_len:
            return False
        return True

    def extract_random_words(
        self,
        count_words: int | None = None,
        level: str | None = None,
    ) -> list[str]:
        """Извлечение указанного количества случайных слов из файла."""
        target_level = level or self._level
        words = list(self._word_generator(target_level))
        target_count = count_words or self._count_words
        return random.sample(words, min(target_count, len(words)))

    def return_char_random_words(
        self, random_words: list[str], level: str | None = None
    ) -> list[str]:
        """Преобразует список слов в список символов с добавлением пунктуации между словами."""
        if not random_words:
            return []

        target_level = level or self._level
        punctuation_list = self._cached_punctuation[target_level]
        probability = self._cached_probability[target_level]

        char_words = []
        last_index = len(random_words) - 1

        for i, word in enumerate(random_words):
            char_words.extend(list(word))
            if i < last_index:
                if random.random() < probability:
                    char_words.append(random.choice(punctuation_list))
                else:
                    char_words.append(" ")

        return char_words

    def return_string_random_words(
        self, random_words: list[str], level: str | None = None
    ) -> str:
        """Преобразует список слов в строку с добавлением пунктуации между словами."""
        if not random_words:
            return ""

        target_level = level or self._level
        punctuation_list = self._cached_punctuation[target_level]
        probability = self._cached_probability[target_level]

        parts = []
        last_index = len(random_words) - 1

        for i, word in enumerate(random_words):
            parts.append(word)
            if i < last_index:
                if random.random() < probability:
                    parts.append(random.choice(punctuation_list))
                else:
                    parts.append(" ")

        return "".join(parts)

    def random_punctuation_mark(self, level: str | None = None) -> str:
        """Добавление символов пунктуации в список символов."""
        target_level = level or self._level
        if random.random() < self._cached_probability[target_level]:
            return random.choice(self._cached_punctuation[target_level])
        return " "

    def generate_random_text(
        self, count_words: int | None = None, level: str | None = None
    ) -> str:
        """Генерация текста из случайных слов с добавлением символов пунктуации."""
        target_count = count_words or self._count_words
        target_level = level or self._level

        random_words = self.extract_random_words(
            count_words=target_count, level=target_level
        )
        return self.return_string_random_words(random_words, level=target_level)

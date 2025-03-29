from __future__ import annotations
from enum import Enum, auto
from typing import Union


class Language(Enum):
    _ignore_ = ['__current_language']
    ENGLISH = auto()
    HEBREW = auto()

    __current_language: Language = None

    def short_name(self) -> str:
        """Return the short name of the language, e.g., ENGLISH -> 'en'."""
        return self.name[:2].lower()

    def __contains__(self, item):
        return Language.contains(item)

    @classmethod
    def contains(cls, key: str) -> bool:
        """Check if the given key (string) is a valid Language enum member."""
        return any(key.upper() == item.name for item in cls)

    @classmethod
    def from_str(cls, name: Union[int, str]) -> Language:
        """
        Convert a string or an integer to a Language enum.

        - If given a 2-letter short name, return the corresponding Language.
        - If given a digit, return the language at that position (1-based index).
        - Otherwise, fallback to standard Enum lookup.
        """

        if isinstance(name, int):
            try:
                return list(cls)[name - 1]  # 1-based index
            except IndexError:
                raise ValueError(f"Invalid index: {name}. Must be between 1 and {len(cls)}.") from None

        if isinstance(name, str):
            name = name.strip()
            if len(name) == 2:
                for language in cls:
                    if language.short_name() == name.lower():
                        return language
                raise ValueError(f"No matching language for short name: {name}") from None

            if name.isdigit():
                return cls.from_str(int(name))

            try:
                return cls[name.upper()]
            except KeyError:
                raise ValueError(f"Invalid language name: {name}") from None

        raise TypeError(f"Invalid type: {type(name)}. Expected int or str.")

    @classmethod
    def get_default(cls) -> Language:
        """Return the default language."""
        return Language.HEBREW

    @classmethod
    def get_current(cls) -> Language:
        """Return the currently set language."""
        return cls.__current_language or cls.get_default()

    @classmethod
    def set_current(cls, language: Language) -> None:
        """Set the current language."""
        if not isinstance(language, cls):
            raise TypeError(f"Expected instance of {cls}, got {type(language)}")
        cls.__current_language = language

    def __str__(self):
        return self.name.lower()

    def __repr__(self):
        return str(self)

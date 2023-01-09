from enum import auto
from typing import Union

from data.enum_args import EnumArgs


class Language(EnumArgs):
    ENGLISH = auto()
    HEBREW = auto()

    def short_name(self):
        # Return the short name of the language for example ENGLISH -> en
        return self.name[:2].lower()

    @staticmethod
    def contains(key):
        key = key.upper()
        return any(key.upper() == item.name for item in Language)

    @classmethod
    def from_str(cls, name: Union[int, str]):
        try:
            if len(name) == 2:
                return [language for language in Language if language.short_name() == name.lower()][0]
            if name.isdigit():
                name = list(Language)[int(name) - 1].name
        except Exception:
            raise ValueError(f"Enum: {type(cls)} Invalid value: {name}") from None
        return super().from_str(name)

    @staticmethod
    def get_default():
        return _DEFAULT_LANGUAGE

    @staticmethod
    def get_current():
        return _CURRENT_LANGUAGE

    @staticmethod
    def set_current(language):
        # pylint: disable=global-statement
        global _CURRENT_LANGUAGE
        _CURRENT_LANGUAGE = language


_DEFAULT_LANGUAGE = Language.HEBREW
_CURRENT_LANGUAGE = _DEFAULT_LANGUAGE

from enum import Enum


class Language(Enum):
    ENGLISH = "en"
    HEBREW = "he"

    def __str__(self):
        return self.name.lower()

    def __repr__(self):
        return str(self)

    def short_name(self):
        return self.value

    @staticmethod
    def contains(key):
        key = key.upper()
        return any(key.upper() == item.name for item in Language)

    @classmethod
    def from_str(cls, value):
        try:
            if isinstance(value, str):
                if value.isdigit():
                    return Language.ENGLISH
                value = value.upper()
                return cls[value]
        except KeyError:
            pass
        raise ValueError(f"ERROR: got '{value}', value must be a string for enum Language keys or values options")

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

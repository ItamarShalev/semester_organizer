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

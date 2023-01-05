from data.language import Language
from data.case_insensitive_dict import CaseInsensitiveDict


# pylint: disable=line-too-long

data = CaseInsensitiveDict({
    "Test": "בדיקה",
})

_TRANSLATION_METHOD = None


def _(text: str):
    return _TRANSLATION_METHOD(text)


def translate(text: str):
    return _TRANSLATION_METHOD(text)


def english(text: str):
    assert text in data, f"Text not found in dictionary: {text}"
    return text


def hebrew(text: str):
    # Should fail if the text is not in the dictionary
    return data[text]


def config_language_text(language: Language):
    # pylint: disable=global-statement
    global _TRANSLATION_METHOD
    if language is Language.ENGLISH:
        _TRANSLATION_METHOD = english
    elif language is Language.HEBREW:
        _TRANSLATION_METHOD = hebrew

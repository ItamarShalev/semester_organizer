from typing import Optional

from collector.db.db import Database
from data.case_insensitive_dict import CaseInsensitiveDict
from data.language import Language

# pylint: disable=line-too-long

data = CaseInsensitiveDict({
    "Test": "בדיקה",
    "There are no courses in the system, please try again with another campus or year.": "אין קורסים במערכת, אנא נסה שנית עם קמפוס אחר או שנה אחרת.",
    "No schedule possible were found": "לא נמצאה מערכת שעות אפשרית",
    "The schedules were saved in the directory: ": "המערכות שעות נשמרו בתיקייה : ",
    "ERROR: Can't click exit button without choose from the options.": "שגיאה: לא ניתן ללחוץ על כפתור יציאה ללא בחירה מהאפשרויות.",
    "Login window": "חלון התחברות",
    "Username or password is missing, please fill all the fields.": "שם משתמש או סיסמא חסרים, אנא מלא את כל השדות.",
    "Username or password is invalid, please check your input.": "שם משתמש או סיסמא לא תקינים, אנא בדוק את הקלט שלך.",
    "Username": "שם משתמש",
    "Password": "סיסמא",
    "Login": "התחברות",
    'notification': '',
    "Error": "שגיאה",
    "Warning": "אזהרה",
    "Info": "מידע",
    "Exit": "יציאה",
    "OK": "אישור",
    "Summer": "סמסטר אלול",
    "Fall": "סמסטר א'",
    "Spring": "סמסטר ב'",
    "Sunday": "יום ראשון",
    "Monday": "יום שני",
    "Tuesday": "יום שלישי",
    "Wednesday": "יום רביעי",
    "Thursday": "יום חמישי",
    "Friday": "יום שישי",
    "english": "אנגלית",
    "hebrew": "עברית",
    "Personal": "אישי",
    "Lecture": "הרצאה",
    "Lab": "מעבדה",
    "Seminar": "סמינר",
    "Practice": "תרגול",
    "activity type": "סוג פעילות",
    "activity name": "שם פעילות",
    "activity id": "מספר פעילות",
    "day": "יום",
    "start time": "שעת התחלה",
    "end time": "שעת סיום",
    "campus": "קמפוס",
    "year": "שנה",
    "semester": "סמסטר",
    "group": "קבוצה",
    "lecturer": "מרצה",
    "lecturer name": "שם מרצה",
    "lecturer id": "מספר מרצה",
    "course name": "שם קורס",
    "course id": "מספר קורס",
    "course": "קורס",
    "course type": "סוג קורס",
    "course location": "מיקום הקורס",
    "Welcome to the semester organizer!\nPlease choose a language\nThe current language is: ": "ברוכים הבאים למארגן מערכת השעות\nאנא בחר שפה\nהשפה הנוכחית היא: ",
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


def config_language_text(language: Optional[Language] = None):
    if language is None:
        return
        # pylint: disable=global-statement
    global _TRANSLATION_METHOD
    if language is Language.ENGLISH:
        _TRANSLATION_METHOD = english
    elif language is Language.HEBREW:
        _TRANSLATION_METHOD = hebrew

    Database().save_language(language)


def get_default_language() -> Language:
    return Language.HEBREW


def get_current_language() -> Language:
    return Database().get_language() or get_default_language()

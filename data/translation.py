from typing import Optional

from data.case_insensitive_dict import TextCaseInsensitiveDict
from data.language import Language

# pylint: disable=line-too-long

data = TextCaseInsensitiveDict({
    "Test": "בדיקה",
    "There are no courses in the system, please try again with another campus update your database from the server.": "אין קורסים במערכת, אנא נסה שנית עם קמפוס אחר או נסה לעדכן את הבסיס נתונים מהשרת.",
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
    "Annual": "שנתי",
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
    "Lab": "פרויקט",
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
    "option": "אפשרות_מספר",
    "with_{}_learning_days_and_{}_minutes_study_time": "עם_{}_ימי_לימוד_ו{}_דקות_זמן_חלון",
    "all_schedules": "כל_המערכות_שעות",
    "most_spread_days": "הכי_הרבה_ימים",
    "least_spread_days": "הכי_פחות_ימים",
    "least_standby_time": "הכי_פחות_זמן_חלון",
    "Yes": "כן",
    "No": "לא",
    "Select the campus by enter their index:": "בחר קמפוס על ידי הקלדת מספר המזהה שלו:",
    "Enter the campus index: ": "הקלד את המספר המזהה של הקמפוס: ",
    "Select the courses by enter their index:": "בחר קורסים על ידי הקלדת מספר המזהה שלהם:",
    "Enter the courses indexes separated by comma (example: 1,2,20): ": "הקלד את מספרי המזהה של הקורסים מופרדים בפסיק (לדוגמא: 1,2,20): ",
    "Do you want to select favorite lecturers?": "האם ברצונך לבחור מרצים מועדפים?",
    "Enter the option index: ": "הקלד את מספר המזהה של האפשרות: ",
    "Select the favorite teachers for lecture for the course: ": "בחר את המרצים המועדפים להרצאה בקורס: ",
    "Select the favorite teachers for lab / exercise for the course: ": "בחר את המרצים המועדפים למעבדה או תרגול בקורס: ",
    "Enter the teachers indexes separated by comma (example: 1,2,20) or 0 to select all: ": "הקלד את מספרי המזהה של המרצים מופרדים בפסיק (לדוגמא: 1,2,20) או 0 לבחירת כולם: ",
    "Generating schedules...": "מייצר מערכות שעות...",
    "Loading academic activities it may take few seconds...": "טוען פעילויות אקדמיות זה עשוי לקחת מספר שניות...",
    "Lesson": "שעור",
    "Exercise": "תרגיל",
    "Project in Lab": "מעבדה",
    "Project": """פרוייקט-במ"מ""",
    "reshimat hamtana": "רשימת המתנה אין לשבץ",
    "Machon Lev": "מכון לב",
    "Machon Tal": "מכון טל",
    "Machon Lustig": "מכון לוסטיג",
    "Mavchar- Men": """מבח"ר בנים""",
    "Mahar-Tal": """מח"ר-טל תבונה""",
    "Computer Science": "מדעי המחשב",
    "Software Engineering": "הנדסת תוכנה",
    "Infinitesimal Calculus 1": "חשבון אינפני' להנדסה 1",
    "day (.+?)[ :]": "יום (.+?):",
    "Done successfully !": "הפעולה הושלמה בהצלחה !",
    "No schedules were found": "לא נמצאו מערכות שעות אפשריות",
    "the system encountered an error, please contanct the engeniers.": "המערכת נתקלה בשגיאה, אנא צור קשר עם המפתחים.",
    "Missing database, can't continue, please download the database file from the github server and import the database by running :": "אין בסיס נתונים על מנת לשלוף את המידע, נא הורד את בסיס הנתונים משרת הגיטאהב ותריץ את הפעולה הבאה : ",
    "Database path is not a file or doesn't exists, the path given is: ": "נתיב בסיס הנתונים אינו קובץ, נתיב בסיס הנתונים שהתקבל: ",
    "There is only one lecture for this the course %s which is %s, automatic select it.": "יש בחירה יחידה לקורס %s שהיא המרצה %s,ולכן נעשתה בחירה אוטומטית.",
    "Found %d possible schedules": "נמצאו %d מערכות שעות אפשריות",
    "Do you want to print the current settings and see their meaning?": "האם ברצונך להדפיס את ההגדרות הנוכחיות ולראות את המשמעות שלהן?",
    "Do you want to change the current settings?": "האם ברצונך לשנות את ההגדרות הנוכחיות?",
    "Current settings:": "הגדרות נוכחיות:",
    "Attendance required all courses: ": "נדרשת השתתפות בכל הקורסים: ",
    "Explain: Count all the courses as attendance is mandatory": "הסבר: להתייחס לכל הקורסים כאל קורסים עם נוכחות חובה",
    "and there is no possibility of collision with other courses.": "ואין אפשרות להתנגשות עם קורסים אחרים.",
    "Year of study: ": "שנת לימודים: ",
    "Explain: The year of the courses to be selected and collect from the colleage.": "הסבר: הקורסים שייבחרו יהיו מהשנה הזאת.",
    "Semester of study: ": "סמסטר: ",
    "Explain: The semester of the courses to be selected and collect from the colleage.": "הסבר: הקורסים שייבחרו יהיו מהסמסטר הזה.",
    "Show hertzog and yeshiva: ": "הצג קורסים של הרצוג וישיבה תיכונית: ",
    "Explain: Show or don't show the courses for hertzog and yeshiva.": "הסבר: הצג או אל תציג את הקורסים של הרצוג וישיבה תיכונית.",
    "Show only courses with free places: ": "הצג רק קורסים עם מקומות פנויים: ",
    "Explain: Show or don't show the courses that have free places to register.": "הסבר: הצג רק את הקורסים שיש להם מקומות פנויים להרשמה.",
    "Show only courses with the same actual number :": "הצג רק קורסים עם אותו מספר סידורי-קבוצתי: ",
    "Explain: Show or don't show the courses that have the same actual number and related.": "הסבר: הצג רק את הקורסים שיש להם אותו מספר סידורי-קבוצתי וקשורים אחד לשני.",
    "there is no guarantee you will get course that have lecture and exercise you can register.": "אין כאן כל דרך להבטיח שתקבל את הקורס שבו יש הרצאה ותרגול ובשניהם ניתן להירשם.",
    "for example course that have lecture for english speaker and exercise for hebrew speaker.": "לדוגמא קורס שיש לו הרצאה לדוברי אנגלית ותרגול לדוברי עברית.",
    "All week days": "כל ימות השבוע",
    "Show only classes in days : ": "הצג רק כיתות בימים: ",
    "Explain: Show only the courses that have classes in the days you selected.": "הסבר: הצג רק את הקורסים שיש להם שיעורים בימים שבחרת.",
    "Output formats: ": "פורמטי פלט: ",
    "Explain: The output formats the schedules will be saved in.": "הסבר: מערכות השעות יישמרו בפורמטים האלו.",
    "Possible formats: ": "פורמטים אפשריים: ",
    "Explain: ": "הסבר: ",
    "If is set to no, you will ask for each course if you will want to be present.": "אם הגדרת לא, אתה תשאל עבור כל קורס אם תרצה להיות נוכח.",
    "Campus name: ": "שם המכון: ",
    "Not set": "לא מוגדר",
    "Explain: The name of the campus that you want to search for the courses.": "הסבר: שם המכון שבו תרצה לחפש את הקורסים.",
})


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

    Language.set_current(language)


_TRANSLATION_METHOD = english

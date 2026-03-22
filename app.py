import logging
import os
import shutil
import traceback
from collections import defaultdict
from typing import List, Dict, Set, Optional

from flask import Flask, render_template, jsonify, request, send_file, session

from src import utils
from src.algorithms.csp import CSP, Status
from src.controller.controller import Controller
from src.collector.db import Database
from src.collector.network import Network, WeakNetworkConnectionException, InvalidSemesterTimeRequestException
from src.data.academic_activity import AcademicActivity
from src.data.activity import Activity
from src.data.course import Course
from src.data.course_choice import CourseChoice
from src.data.degree import Degree
from src.data.day import Day
from src.data.language import Language
from src.data.meeting import Meeting
from src.data.schedule import Schedule
from src.data.semester import Semester
from src.data.settings import Settings
from src.data.output_format import OutputFormat
from src.data.translation import _
from src.data.user import User

app_resources = utils.SRC_PATH / 'app'

app = Flask(
    __name__,
    template_folder=app_resources / 'templates',
    static_folder=app_resources / 'static',
)
app.secret_key = os.urandom(24)
db = Database()
utils.config_logging_level(logging.DEBUG)
logger = utils.get_logging()


def get_settings() -> Settings:
    settings = db.load_settings()
    if not settings:
        settings = Settings()
    return settings


def save_and_return_settings(settings: Settings) -> dict:
    db.save_settings(settings)
    return settings_to_dict(settings)


def settings_to_dict(settings: Settings) -> dict:
    return {
        "attendance_required_all_courses": settings.attendance_required_all_courses,
        "campus_name": settings.campus_name,
        "year": settings.year,
        "semester": settings.semester.name,
        "degrees": [d.name for d in settings.degrees],
        "show_hertzog_and_yeshiva": settings.show_hertzog_and_yeshiva,
        "show_only_courses_with_free_places": settings.show_only_courses_with_free_places,
        "show_only_courses_active_classes": settings.show_only_courses_active_classes,
        "show_only_courses_with_the_same_actual_number": settings.show_only_courses_with_the_same_actual_number,
        "dont_show_courses_already_done": settings.dont_show_courses_already_done,
        "show_only_classes_in_days": [d.name for d in settings.show_only_classes_in_days],
        "output_formats": [f.name for f in settings.output_formats],
        "show_only_classes_can_enroll": settings.show_only_classes_can_enroll,
        "show_only_courses_with_prerequisite_done": settings.show_only_courses_with_prerequisite_done,
        "language": settings.language.name,
        "show_english_speaker_courses": settings.show_english_speaker_courses,
    }


# ─── Pages ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    language = Language.HEBREW
    Language.set_current(language)
    settings = get_settings()
    settings.language = language
    settings.year = utils.convert_year(settings.year, language)
    db.save_settings(settings)

    degrees: List[Degree] = db.load_degrees()
    degrees_data = [{"name": degree.name, "display": _(degree.name)} for degree in degrees]
    campuses = db.get_common_campuses_names()
    semesters = [{"name": s.name, "display": _(str(s))} for s in Semester]
    days = [{"name": d.name, "display": _(str(d))} for d in Day]
    output_formats_list = [{"name": f.name, "display": _(f.name.capitalize()) if f.name.capitalize() in ["Csv", "Excel", "Image"] else f.name}
                           for f in OutputFormat]
    # Fix display names
    output_formats_list = []
    for f in OutputFormat:
        if f == OutputFormat.CSV:
            display = _("CSV")
        elif f == OutputFormat.EXCEL:
            display = _("Excel")
        else:
            display = _("Image")
        output_formats_list.append({"name": f.name, "display": display})

    return render_template(
        "index.html",
        degrees=degrees_data,
        campuses=campuses,
        semesters=semesters,
        days=days,
        output_formats=output_formats_list,
        settings=settings_to_dict(settings),
    )


# ─── Settings API ────────────────────────────────────────────────────────────

@app.route("/api/settings", methods=["GET"])
def api_get_settings():
    settings = get_settings()
    return jsonify(settings_to_dict(settings))


@app.route("/api/settings", methods=["POST"])
def api_update_settings():
    data = request.json
    settings = get_settings()

    if "attendance_required_all_courses" in data:
        settings.attendance_required_all_courses = data["attendance_required_all_courses"]
    if "campus_name" in data:
        settings.campus_name = data["campus_name"]
    if "semester" in data:
        settings.semester = Semester[data["semester"].upper()]
    if "degrees" in data:
        settings.degrees = {Degree[d] for d in data["degrees"]}
    if "show_hertzog_and_yeshiva" in data:
        settings.show_hertzog_and_yeshiva = data["show_hertzog_and_yeshiva"]
    if "show_only_courses_with_free_places" in data:
        settings.show_only_courses_with_free_places = data["show_only_courses_with_free_places"]
    if "show_only_courses_active_classes" in data:
        settings.show_only_courses_active_classes = data["show_only_courses_active_classes"]
    if "show_only_courses_with_the_same_actual_number" in data:
        settings.show_only_courses_with_the_same_actual_number = data["show_only_courses_with_the_same_actual_number"]
    if "dont_show_courses_already_done" in data:
        settings.dont_show_courses_already_done = data["dont_show_courses_already_done"]
    if "show_only_classes_in_days" in data:
        settings.show_only_classes_in_days = [Day[d.upper()] for d in data["show_only_classes_in_days"]]
    if "output_formats" in data:
        settings.output_formats = [OutputFormat[f.upper()] for f in data["output_formats"]]
    if "show_only_classes_can_enroll" in data:
        settings.show_only_classes_can_enroll = data["show_only_classes_can_enroll"]
    if "show_only_courses_with_prerequisite_done" in data:
        settings.show_only_courses_with_prerequisite_done = data["show_only_courses_with_prerequisite_done"]
    if "show_english_speaker_courses" in data:
        settings.show_english_speaker_courses = data["show_english_speaker_courses"]

    return jsonify(save_and_return_settings(settings))


# ─── Auth API ────────────────────────────────────────────────────────────────

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"success": False, "message": _("Username or password is missing, please fill all the fields.")}), 400

    user = User(username, password)
    network = Network(user)

    try:
        connected = network.check_connection()
    except Exception as e:
        logger.error("Login error: %s", str(e))
        return jsonify({"success": False, "message": _("Username or password is invalid, please check your input.")}), 401

    if connected:
        db.save_user_data(user)
        session["logged_in"] = True
        session["username"] = username
        return jsonify({"success": True, "message": _("Your user details are correct and can continue.")})
    else:
        return jsonify({"success": False, "message": _("Username or password is invalid, please check your input.")}), 401


@app.route("/api/login/microsoft", methods=["POST"])
def api_login_microsoft():
    """
    Handle Microsoft OAuth login for Levnet.
    Uses Playwright to automate the Microsoft login flow.
    """
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"success": False, "message": _("Username or password is missing, please fill all the fields.")}), 400

    try:
        cookies = _microsoft_login_with_playwright(username, password)
        if cookies:
            user = User(username, password)
            db.save_user_data(user)
            session["logged_in"] = True
            session["username"] = username
            session["ms_cookies"] = cookies
            return jsonify({"success": True, "message": _("Your user details are correct and can continue.")})
        else:
            return jsonify({"success": False, "message": _("Username or password is invalid, please check your input.")}), 401
    except Exception as e:
        logger.error("Microsoft login error: %s\n%s", str(e), traceback.format_exc())
        return jsonify({"success": False, "message": str(e)}), 500


def _microsoft_login_with_playwright(username: str, password: str) -> Optional[list]:
    """Use Playwright to handle Microsoft OAuth login and return session cookies."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError("Playwright is not installed. Run: pip install playwright && playwright install")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            page.goto("https://levnet.jct.ac.il", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=15000)

            # Check if redirected to Microsoft login
            current_url = page.url
            if "login.microsoftonline.com" in current_url or "login.microsoft.com" in current_url:
                # Microsoft OAuth flow
                page.fill('input[type="email"], input[name="loginfmt"]', username, timeout=10000)
                page.click('input[type="submit"], button[type="submit"]')
                page.wait_for_load_state("networkidle", timeout=10000)

                page.fill('input[type="password"], input[name="passwd"]', password, timeout=10000)
                page.click('input[type="submit"], button[type="submit"]')
                page.wait_for_load_state("networkidle", timeout=15000)

                # Handle "Stay signed in?" prompt
                try:
                    page.click('input[type="submit"], button[type="submit"]', timeout=5000)
                except Exception:
                    pass

                page.wait_for_load_state("networkidle", timeout=15000)

            elif "levnet.jct.ac.il" in current_url:
                # Check if there's a Microsoft login button on the page
                ms_button = page.query_selector('a[href*="microsoft"], button:has-text("Microsoft"), a:has-text("Microsoft"), .ms-login, [data-provider="microsoft"]')
                if ms_button:
                    ms_button.click()
                    page.wait_for_load_state("networkidle", timeout=15000)

                    if "login.microsoftonline.com" in page.url or "login.microsoft.com" in page.url:
                        page.fill('input[type="email"], input[name="loginfmt"]', username, timeout=10000)
                        page.click('input[type="submit"], button[type="submit"]')
                        page.wait_for_load_state("networkidle", timeout=10000)

                        page.fill('input[type="password"], input[name="passwd"]', password, timeout=10000)
                        page.click('input[type="submit"], button[type="submit"]')
                        page.wait_for_load_state("networkidle", timeout=15000)

                        try:
                            page.click('input[type="submit"], button[type="submit"]', timeout=5000)
                        except Exception:
                            pass

                        page.wait_for_load_state("networkidle", timeout=15000)

            # Verify we're logged in by checking cookies
            cookies = context.cookies()
            levnet_cookies = [c for c in cookies if "jct.ac.il" in c.get("domain", "")]

            if levnet_cookies:
                return levnet_cookies
            return None

        finally:
            browser.close()


@app.route("/api/login/status", methods=["GET"])
def api_login_status():
    user = db.load_user_data()
    logged_in = bool(user)
    username = user.username if user else ""
    return jsonify({"logged_in": logged_in, "username": username})


@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.pop("logged_in", None)
    session.pop("username", None)
    session.pop("ms_cookies", None)
    return jsonify({"success": True})


# ─── Data API ────────────────────────────────────────────────────────────────

@app.route("/api/degrees", methods=["GET"])
def api_get_degrees():
    degrees = db.load_degrees()
    return jsonify([{"name": d.name, "display": _(d.name)} for d in degrees])


@app.route("/api/campuses", methods=["GET"])
def api_get_campuses():
    campuses = db.get_common_campuses_names()
    return jsonify(sorted(campuses))


@app.route("/api/courses", methods=["POST"])
def api_get_courses():
    data = request.json
    degrees_names = data.get("degrees", [])
    campus = data.get("campus", "")

    if not degrees_names or not campus:
        return jsonify([])

    degrees = {Degree[d] for d in degrees_names}
    settings = get_settings()
    settings.campus_name = campus
    settings.degrees = degrees
    db.save_settings(settings)

    courses: List[Course] = db.load_courses(Language.get_current(), degrees)
    courses_data = []
    for course in sorted(courses, key=lambda c: c.name):
        courses_data.append({
            "name": course.name,
            "course_number": course.course_number,
            "parent_course_number": course.parent_course_number,
            "is_active": course.is_active,
            "credits": course.credits_count,
        })
    return jsonify(courses_data)


@app.route("/api/course_lecturers", methods=["POST"])
def api_get_course_lecturers():
    """Get available lecturers for selected courses."""
    data = request.json
    degrees_names = data.get("degrees", [])
    campus = data.get("campus", "")
    courses_names = data.get("courses", [])

    if not degrees_names or not campus or not courses_names:
        return jsonify({})

    degrees = {Degree[d] for d in degrees_names}
    settings = get_settings()
    settings.campus_name = campus
    settings.degrees = degrees

    language = Language.get_current()
    courses = db.load_courses(language, degrees)
    selected_courses = [c for c in courses if c.name in courses_names]

    parent_courses_ids = {c.parent_course_number for c in selected_courses}
    activities = db.load_activities_by_parent_courses_numbers(parent_courses_ids, campus, language, degrees, settings)

    # Group by course name, then by type
    result = {}
    for activity in activities:
        if activity.name not in result:
            result[activity.name] = {"lecture": set(), "practice": set()}
        if activity.type.is_lecture():
            result[activity.name]["lecture"].add(activity.lecturer_name)
        else:
            result[activity.name]["practice"].add(activity.lecturer_name)

    # Convert sets to sorted lists
    for name in result:
        result[name]["lecture"] = sorted(result[name]["lecture"])
        result[name]["practice"] = sorted(result[name]["practice"])

    return jsonify(result)


# ─── Courses Already Done API ─────────────────────────────────────────────────

@app.route("/api/courses_already_done", methods=["GET"])
def api_get_courses_already_done():
    language = Language.get_current()
    courses = db.load_courses_already_done(language)
    return jsonify([{"name": c.name, "parent_course_number": c.parent_course_number} for c in courses])


@app.route("/api/courses_already_done", methods=["POST"])
def api_set_courses_already_done():
    data = request.json
    course_numbers = data.get("parent_course_numbers", [])

    language = Language.get_current()
    all_courses = db.load_courses(language)

    courses_to_save = {c for c in all_courses if c.parent_course_number in course_numbers}
    db.clear_courses_already_done()
    if courses_to_save:
        db.save_courses_already_done(courses_to_save)

    return jsonify({"success": True})


@app.route("/api/courses_already_done/extract", methods=["POST"])
def api_extract_courses_already_done():
    """Extract courses already done from Levnet."""
    user = db.load_user_data()
    if not user:
        return jsonify({"success": False, "message": _("Need to login to Levnet to use this feature.")}), 401

    network = Network(user)
    try:
        network.connect()
        courses_done = network.extract_courses_already_did()
        # Save to database
        language = Language.get_current()
        all_courses = db.load_courses(language)
        matching_courses = set()
        for course in all_courses:
            for course_name, course_number in courses_done:
                if course.course_number == course_number:
                    matching_courses.add(course)
                    break
        db.save_courses_already_done(matching_courses)
        network.disconnect()
        return jsonify({
            "success": True,
            "courses": [{"name": c.name, "parent_course_number": c.parent_course_number} for c in matching_courses]
        })
    except Exception as e:
        logger.error("Extract courses error: %s", str(e))
        return jsonify({"success": False, "message": str(e)}), 500


# ─── Personal Activities API ──────────────────────────────────────────────────

@app.route("/api/personal_activities", methods=["GET"])
def api_get_personal_activities():
    activities = db.load_personal_activities()
    result = []
    for activity in activities:
        meetings = []
        for m in activity.meetings:
            meetings.append({
                "day": m.day.name,
                "start_time": m.get_string_start_time(),
                "end_time": m.get_string_end_time(),
            })
        result.append({
            "id": activity.activity_id,
            "name": activity.name,
            "meetings": meetings,
        })
    return jsonify(result)


@app.route("/api/personal_activities", methods=["POST"])
def api_save_personal_activity():
    data = request.json
    name = data.get("name", "").strip()
    meetings_data = data.get("meetings", [])

    if not name:
        return jsonify({"success": False, "message": _("Please enter an activity name")}), 400
    if not meetings_data:
        return jsonify({"success": False, "message": _("Please choose at least one day.")}), 400

    db.init_personal_database_tables()
    activity = Activity()
    activity.name = name

    meetings = []
    for m in meetings_data:
        try:
            meeting = Meeting(Day[m["day"].upper()], m["start_time"], m["end_time"])
            meetings.append(meeting)
        except Exception as e:
            return jsonify({"success": False, "message": _("Invalid time format, please try again.")}), 400

    activity.meetings = meetings
    db.save_personal_activities([activity])

    return jsonify({"success": True})


@app.route("/api/personal_activities/<int:activity_id>", methods=["DELETE"])
def api_delete_personal_activity(activity_id):
    db.delete_personal_activity(activity_id)
    return jsonify({"success": True})


# ─── Activities Can Enroll API ──────────────────────────────────────────────

@app.route("/api/activities_can_enroll", methods=["POST"])
def api_extract_activities_can_enroll():
    """Extract activities the student can enroll in from Levnet."""
    user = db.load_user_data()
    if not user:
        return jsonify({"success": False, "message": _("Need to login to Levnet to use this feature.")}), 401

    network = Network(user)
    settings = get_settings()

    try:
        network.connect()
        parent_courses_already_did = [c.parent_course_number for c in db.load_courses_already_done(Language.get_current())]
        activities_ids = network.extract_all_activities_ids_can_enroll_in(settings, parent_courses_already_did)
        db.save_activities_ids_groups_can_enroll_in(activities_ids)
        network.disconnect()
        return jsonify({
            "success": True,
            "count": len(activities_ids),
            "message": _("Extract all activities can enroll successfully.")
        })
    except InvalidSemesterTimeRequestException:
        return jsonify({"success": False, "message": _("Registration isn't available, it's not the registration period.")}), 400
    except Exception as e:
        logger.error("Extract activities error: %s", str(e))
        return jsonify({"success": False, "message": str(e)}), 500


# ─── Schedule Generation API ─────────────────────────────────────────────────

@app.route("/api/generate", methods=["POST"])
def api_generate():
    data = request.json
    degrees_names = data.get("degrees", [])
    campus = data.get("campus", "")
    courses_data = data.get("courses", [])
    lecturer_prefs = data.get("lecturer_preferences", {})
    attendance_prefs = data.get("attendance_preferences", {})

    if not degrees_names or not campus or not courses_data:
        return jsonify({"success": False, "message": "נא לבחור תואר, קמפוס וקורסים"}), 400

    settings = get_settings()
    degrees = {Degree[d] for d in degrees_names}
    settings.campus_name = campus
    settings.degrees = degrees
    db.save_settings(settings)

    language = Language.get_current()
    courses = db.load_courses(language, degrees)
    selected_courses = [c for c in courses if c.name in courses_data]

    if not selected_courses:
        return jsonify({"success": False, "message": "לא נמצאו קורסים שנבחרו"}), 400

    parent_courses_ids = {c.parent_course_number for c in selected_courses}
    activities = db.load_activities_by_parent_courses_numbers(parent_courses_ids, campus, language, degrees, settings)

    # Build course choices with lecturer preferences
    courses_choices = {}
    for course in selected_courses:
        course_activities = [a for a in activities if a.parent_course_number == course.parent_course_number]
        lecture_teachers = set()
        practice_teachers = set()
        for a in course_activities:
            if a.type.is_lecture():
                lecture_teachers.add(a.lecturer_name)
            else:
                practice_teachers.add(a.lecturer_name)

        # Apply lecturer preferences if provided
        pref = lecturer_prefs.get(course.name, {})
        fav_lectures = set(pref.get("lecture", [])) if pref.get("lecture") else lecture_teachers
        fav_practices = set(pref.get("practice", [])) if pref.get("practice") else practice_teachers

        # Apply attendance preferences
        att_pref = attendance_prefs.get(course.name, {})
        att_lecture = att_pref.get("lecture", True)
        att_practice = att_pref.get("practice", True)

        course_choice = CourseChoice(
            course.name,
            course.parent_course_number,
            fav_lectures,
            fav_practices,
            att_lecture,
            att_practice,
        )
        courses_choices[course.name] = course_choice

    # Load activities that can be enrolled in
    activities_ids_groups = db.load_activities_ids_groups_can_enroll_in()
    courses_degrees = db.load_degrees_courses()

    csp = CSP()
    schedules: List[Schedule] = csp.extract_schedules(activities, courses_choices, settings, activities_ids_groups,
                                                       courses_degrees)
    status = csp.get_status()

    if status is Status.FAILED or not schedules:
        crash_info = ""
        first_name, second_name = csp.get_last_activities_crashed()
        if first_name and second_name:
            crash_info = f"\n{_('The activity: {} And {}').format(first_name, second_name)}"
        return jsonify({
            "success": False,
            "message": _("No schedules were found") + crash_info,
            "status": status.name,
        }), 400

    # Save schedules
    results_path = utils.get_results_path()
    Controller.save_schedules(schedules, settings, results_path)

    # Create ZIP
    zip_file = results_path.parent / "semester_organizer_generated_schedules.zip"
    zip_file.unlink(missing_ok=True)
    shutil.make_archive(str(zip_file).replace(".zip", ""), 'zip', results_path)
    session["zip"] = str(zip_file)

    status_message = ""
    if status is Status.SUCCESS_WITH_ONE_FAVORITE_LECTURER:
        status_message = _("No schedules were found with all favorite lecturers, but found with some of them")
    elif status is Status.SUCCESS_WITHOUT_FAVORITE_LECTURERS:
        status_message = _("No schedules were found with favorite lecturers")

    return jsonify({
        "success": True,
        "message": f"נוצרו {len(schedules)} מערכות שעות בהצלחה",
        "count": len(schedules),
        "status": status.name,
        "status_message": status_message,
    })


@app.route("/api/download", methods=["POST"])
def api_download():
    if "zip" not in session:
        return jsonify({"message": "לא נמצא קובץ להורדה"}), 400
    return send_file(session["zip"], as_attachment=True)


# ─── Legacy endpoints (backward compatibility) ───────────────────────────────

@app.route("/generate", methods=["POST"])
def generate():
    """Legacy endpoint - redirects to new API."""
    data = request.json
    degrees_names = data.get("degrees", [])
    campus = data.get("campus", "")
    courses_names = data.get("courses", [])

    if not degrees_names or not campus or not courses_names:
        return jsonify({"message": "נא לבחור תואר, קמפוס וקורסים"}), 400

    degrees = {degree for degree in db.load_degrees() if _(degree.name) in degrees_names}
    courses = db.load_courses(Language.get_current(), degrees)
    courses = [course for course in courses if course.name in courses_names]

    settings = get_settings()
    settings.output_formats = [OutputFormat.IMAGE]
    settings.campus_name = campus
    settings.degrees = degrees
    db.save_settings(settings)
    parent_courses_ids = {course.parent_course_number for course in courses}
    language = settings.language
    activities = db.load_activities_by_parent_courses_numbers(parent_courses_ids, campus, language, degrees, settings)
    csp = CSP()
    schedules: List[Schedule] = csp.extract_schedules(activities, settings=settings)

    status = csp.get_status()
    if status is Status.FAILED or not schedules:
        return jsonify({"message": "לא היה ניתן ליצור מערכת שעות, נא לבחור קורסים אחרים."}), 400

    results_path = utils.get_results_path()
    Controller.save_schedules(schedules, settings, results_path)

    zip_file = results_path.parent / "semester_organizer_generated_schedules.zip"
    zip_file.unlink(missing_ok=True)
    shutil.make_archive(str(zip_file).replace(".zip", ""), 'zip', results_path)
    session["zip"] = str(zip_file)

    return jsonify({"message": "נוצר בהצלחה", "zip": str(zip_file)})


@app.route("/download_zip", methods=["POST"])
def download_zip():
    if "zip" not in session:
        return jsonify({"message": "לא נמצא קובץ להורדה"}), 400
    return send_file(session["zip"], as_attachment=True)


@app.route("/get_campuses", methods=["POST"])
def get_campuses():
    selected_degrees = request.json.get("degrees", [])
    if not selected_degrees:
        return jsonify([])
    campuses = db.get_common_campuses_names()
    return jsonify(sorted(campuses))


@app.route("/get_courses", methods=["POST"])
def get_courses():
    degrees_names: List[str] = request.json["degrees"]
    campus: str = request.json["campus"]
    degrees = {degree for degree in db.load_degrees() if _(degree.name) in degrees_names}

    setting = get_settings()
    setting.campus_name = campus
    setting.degrees = degrees
    db.save_settings(setting)

    courses: List[Course] = db.load_courses(Language.get_current(), degrees)
    courses_names = list(sorted([course.name for course in courses]))
    return jsonify(courses_names)


if __name__ == "__main__":
    app.run(debug=True, port=5000)

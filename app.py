import logging
import os
import shutil
from pathlib import Path
from typing import List

from flask import Flask, render_template, jsonify, request, send_file, session

from src import utils
from src.algorithms.csp import CSP, Status
from src.controller.controller import Controller
from src.collector.db import Database
from src.data.degree import Degree
from src.data.course import Course
from src.data.language import Language
from src.data.schedule import Schedule
from src.data.settings import Settings
from src.data.output_format import OutputFormat
from src.data.translation import _

app_resources = Path(__file__).parent / 'app'

app = Flask(
    __name__,
    template_folder=app_resources / 'templates',
    static_folder=app_resources / 'static'
)
app.secret_key = os.urandom(24)
db = Database()
utils.config_logging_level(logging.DEBUG)


@app.route("/")
def index():
    language = Language.HEBREW
    Language.set_current(language)
    settings = Settings()
    settings.language = language
    settings.year = utils.convert_year(settings.year, language)
    degrees: List[Degree] = db.load_degrees()
    degrees_names: List[str] = [_(degree.name) for degree in degrees]
    db.save_settings(settings)
    return render_template("index.html", degrees=degrees_names)


@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    degrees_names = data.get("degrees", [])
    campus = data.get("campus", "")
    courses_names = data.get("courses", [])
    logger = session.get("logger", utils.get_logging())
    logger.info(f"Generating schedules for degrees: {degrees_names}, campus: {campus}, courses: {courses_names}")

    if not degrees_names or not campus or not courses_names:
        return jsonify({"message": "נא לבחור תואר, קמפוס וקורסים"}), 400

    degrees = {degree for degree in db.load_degrees() if _(degree.name) in degrees_names}
    courses = db.load_courses(Language.get_current(), degrees)
    courses = [course for course in courses if course.name in courses_names]

    settings = db.load_settings()
    settings.output_formats = [OutputFormat.IMAGE]
    settings.campus_name = campus
    settings.degrees = degrees
    db.save_settings(settings)
    parent_courses_ids = {course.parent_course_number for course in courses}
    language = settings.language
    activities = db.load_activities_by_parent_courses_numbers(parent_courses_ids, campus, language, degrees, settings)
    csp = CSP()
    schedules: List[Schedule] = csp.extract_schedules(activities, settings=settings)
    logger.info(f"Finished extracting schedules, total schedules: {len(schedules)}")
    status = csp.get_status()
    if status is Status.FAILED or not schedules:
        return jsonify({"message": "לא היה ניתן ליצור מערכת שעות, נא לבחור קורסים אחרים."}), 400

    results_path = utils.get_results_path()
    Controller.save_schedules(schedules, settings, results_path)
    logger.info("Finished saving schedules")
    # Create a ZIP file
    message = _("The schedules were saved in the directory: ") + str(results_path)
    logger.info(message)
    zip_file = results_path.parent / "semester_organizer_generated_schedules.zip"
    zip_file.unlink(missing_ok=True)

    shutil.make_archive(str(zip_file).replace(".zip", ""), 'zip', results_path)
    session["zip"] = str(zip_file)

    return jsonify({
        "message": "נוצר בהצלחה",
        "zip": str(zip_file)
    })


@app.route("/download_zip", methods=["POST"])
def download_zip():
    if "zip" not in session:
        return jsonify({"message": "לא נמצא קובץ להורדה"}), 400
    return send_file(session["zip"], as_attachment=True)


def create_garbage_file(file_path):
    """Generate a fake PNG file with random garbage data."""
    with open(file_path, "wb") as f:
        f.write(os.urandom(1024))  # Create a 1KB garbage file


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

    setting = db.load_settings()
    setting.campus_name = campus
    setting.degrees = degrees
    db.save_settings(setting)

    courses: List[Course] = db.load_courses(Language.get_current(), degrees)
    courses_names = list(sorted([course.name for course in courses]))
    return jsonify(courses_names)


if __name__ == "__main__":
    app.run(debug=True, port=5000)

from data.type import Type


class Course:

    def __init__(self, name: str, course_number: int, parent_course_number: int, activity_id: str = None):
        """
        :param activity_id: can be None if the course is not an active activity
        """
        self.name = name
        self.course_number = course_number
        self.parent_course_number = parent_course_number
        self.attendance_required = {type: True for type in [Type.LECTURE, Type.PRACTICE, Type.LAB]}
        self.activity_id = activity_id

    def __eq__(self, other):
        if self.activity_id and other.activity_id:
            return self.activity_id == other.activity_id
        is_equals = self.name == other.name
        is_equals = is_equals and self.course_number == other.course_number
        is_equals = is_equals and self.parent_course_number == other.parent_course_number
        return is_equals

    def __hash__(self):
        return hash((self.name, self.course_number, self.parent_course_number))

    def set_attendance_required(self, course_type: Type, required: bool):
        self.attendance_required[course_type] = required

    def __str__(self):
        return f"{self.name} {self.course_number} {self.parent_course_number}"

    def __repr__(self):
        return str(self)

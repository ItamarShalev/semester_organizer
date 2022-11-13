

class Course:

    def __init__(self, name: str, course_number: int, parent_course_number: int):
        self.name = name
        self.course_number = course_number
        self.parent_course_number = parent_course_number

    def __eq__(self, other):
        is_equals = self.name == other.name
        is_equals = is_equals and self.course_number == other.course_number
        is_equals = is_equals and self.parent_course_number == other.parent_course_number
        return is_equals

    def __str__(self):
        return f"{self.name} {self.course_number} {self.parent_course_number}"

import activity


class AcademicActivity(activity.Activity):
    def __init__(self):
        super().__init__()
        self.lecturer_name = None
        self.course_number = None
        self.parent_course_number = None
        self.location = None

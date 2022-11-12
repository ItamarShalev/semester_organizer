class Activity:

    def __init__(self):
        self.name = None
        self.type = None
        self.is_must = False
        self.days = [[]] * 7

    def add_slot(self, meeting):
        self.days[meeting.day.value] += meeting

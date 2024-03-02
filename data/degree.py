from aenum import Enum, NoAlias


class Degree(Enum):
    # name, department
    _settings_ = NoAlias

    COMPUTER_SCIENCE = 20
    SOFTWARE_ENGINEERING = 20
    BIOINFORMATICS = 11

    def __str__(self):
        # For example COMPUTER_SCIENCE -> Computer Science
        return self.name.replace("_", " ").title()

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(self.name)

    def __iter__(self):
        return iter((self.name, self.value))

    def __eq__(self, other):
        return self.name == other.name

    @staticmethod
    def get_defaults():
        return {Degree.COMPUTER_SCIENCE, Degree.SOFTWARE_ENGINEERING}

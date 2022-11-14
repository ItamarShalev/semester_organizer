

class User:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

    def __eq__(self, other):
        return self.username == other.username and self.password == other.password

    def __str__(self):
        return f"{self.username} {self.password}"

    def __repr__(self):
        return str(self)

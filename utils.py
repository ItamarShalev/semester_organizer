import os


def get_root_path():
    return os.path.dirname(os.path.abspath(__file__))


def get_database_path():
    if not os.path.exists(os.path.join(get_root_path(), "database")):
        os.makedirs(os.path.join(get_root_path(), "database"))
    return os.path.join(get_root_path(), "database")

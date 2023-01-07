import logging
import utils
from data import translation
from data.language import Language


def pytest_configure(config):
    """
    Allows plugins and conftest files to perform initial configuration.
    This hook is called for every plugin and initial conftest
    file after command line options have been parsed.
    """
    utils.init_project()
    utils.config_logging_level(logging.DEBUG)
    translation.config_language_text(Language.get_default())

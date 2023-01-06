import logging

import utils
from controller.controller import Controller
from data import translation

if __name__ == '__main__':
    utils.init_project()
    utils.config_logging_level(logging.INFO)
    translation.config_language_text(translation.get_default_language())
    Controller().run_main_gui_flow()

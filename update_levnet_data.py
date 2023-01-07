import logging

import utils
from controller.controller import Controller
from data import translation
from data.language import Language

if __name__ == '__main__':
    translation.config_language_text(Language.ENGLISH)
    utils.init_project()
    utils.config_logging_level(logging.DEBUG)
    Controller().run_update_levnet_data_flow()

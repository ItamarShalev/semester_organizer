import logging

import utils
from controller.controller import Controller

if __name__ == '__main__':
    utils.config_logging_level(logging.INFO)
    Controller().run_main_gui_flow()

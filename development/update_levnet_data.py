import logging

import utils
from controller.controller import Controller

if __name__ == '__main__':
    utils.init_project()
    utils.config_logging_level(logging.DEBUG)
    Controller().run_update_levnet_data_flow()

import logging

import utils
from controller.controller import Controller

if __name__ == '__main__':
    utils.set_logging_to_file(logging.DEBUG)
    Controller().run_update_levnet_data_flow()

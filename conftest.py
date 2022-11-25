from unittest import TestCase
import logging
import utils


class TestClass(TestCase):
    prefix_suffix = "*" * 45

    @classmethod
    def setUpClass(cls):
        cls.logger = utils.get_logging()
        message = f"\n{cls.prefix_suffix} Starting test class: {cls.__name__} {cls.prefix_suffix}"
        cls.logger.debug(message)

    def setUp(self):
        message = f"\n{self.prefix_suffix} Starting test: {self._testMethodName} {self.prefix_suffix}"
        self.logger.debug(message)

    def tearDown(self):
        status = "Succeed" if self._outcome.success else "Failed"
        message = f"\n{self.prefix_suffix} Finished test: {self._testMethodName} : {status} {self.prefix_suffix}"
        self.logger.debug(message)


def pytest_configure(config):
    """
    Allows plugins and conftest files to perform initial configuration.
    This hook is called for every plugin and initial conftest
    file after command line options have been parsed.
    """
    utils.init_project()
    utils.config_logging_level(logging.DEBUG)

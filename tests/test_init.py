# -*- encoding: utf-8 -*-
"""
Tests for keria.__init__ module
"""

import logging
import unittest
from unittest.mock import Mock
import keria


class TestKeriaInit(unittest.TestCase):
    """Test cases for keria.__init__ module"""

    def test_module_attributes_exist(self):
        """Test that required module attributes are defined"""
        self.assertTrue(hasattr(keria, "__version__"))
        self.assertTrue(hasattr(keria, "log_name"))
        self.assertTrue(hasattr(keria, "log_format_str"))
        self.assertTrue(hasattr(keria, "ogler"))
        self.assertTrue(hasattr(keria, "keriLogger"))
        self.assertTrue(hasattr(keria, "set_log_level"))

    def test_version_format(self):
        """Test that version follows semantic versioning pattern"""
        version = keria.__version__
        self.assertIsInstance(version, str)
        # Basic check for version format (x.y.z)
        parts = version.split(".")
        self.assertEqual(len(parts), 3)
        for part in parts:
            self.assertTrue(part.isdigit())

    def test_log_name_is_keria(self):
        """Test that log_name is set to 'keria'"""
        self.assertEqual(keria.log_name, "keria")

    def test_log_format_string_contains_expected_fields(self):
        """Test that log format string contains expected logging fields"""
        format_str = keria.log_format_str
        expected_fields = [
            "%(asctime)s",
            "%(levelname)-8s",
            "%(module)s",
            "%(funcName)s",
            "%(lineno)s",
            "%(message)s",
        ]
        for field in expected_fields:
            self.assertIn(field, format_str)
        # Check that it contains the keria prefix
        self.assertIn("[keria]", format_str)

    def test_ogler_initialization(self):
        """Test that ogler is properly initialized"""
        self.assertIsNotNone(keria.ogler)
        self.assertEqual(keria.ogler.level, logging.INFO)

    def test_logger_initialization(self):
        """Test that keriLogger is properly initialized"""
        self.assertIsNotNone(keria.keriLogger)
        self.assertIsInstance(keria.keriLogger, logging.Logger)

    def test_set_log_level_function_exists(self):
        """Test that set_log_level function is callable"""
        self.assertTrue(callable(keria.set_log_level))

    def test_set_log_level_with_debug(self):
        """Test set_log_level function with DEBUG level"""
        mock_logger = Mock()

        # Call the function
        keria.set_log_level("DEBUG", mock_logger)

        # Check that ogler level was set
        self.assertEqual(keria.ogler.level, logging.DEBUG)

        # Check that mock logger had setLevel called
        mock_logger.setLevel.assert_called_with(logging.DEBUG)

    def test_set_log_level_with_info(self):
        """Test set_log_level function with INFO level"""
        mock_logger = Mock()

        # Call the function
        keria.set_log_level("INFO", mock_logger)

        # Check that ogler level was set
        self.assertEqual(keria.ogler.level, logging.INFO)

        # Check that mock logger had setLevel called
        mock_logger.setLevel.assert_called_with(logging.INFO)

    def test_set_log_level_with_warning(self):
        """Test set_log_level function with WARNING level"""
        mock_logger = Mock()

        # Call the function
        keria.set_log_level("WARNING", mock_logger)

        # Check that ogler level was set
        self.assertEqual(keria.ogler.level, logging.WARNING)

        # Check that mock logger had setLevel called
        mock_logger.setLevel.assert_called_with(logging.WARNING)

    def test_set_log_level_with_error(self):
        """Test set_log_level function with ERROR level"""
        mock_logger = Mock()

        # Call the function
        keria.set_log_level("ERROR", mock_logger)

        # Check that ogler level was set
        self.assertEqual(keria.ogler.level, logging.ERROR)

        # Check that mock logger had setLevel called
        mock_logger.setLevel.assert_called_with(logging.ERROR)

    def test_set_log_level_with_lowercase(self):
        """Test set_log_level function handles lowercase input"""
        mock_logger = Mock()

        # Call the function with lowercase
        keria.set_log_level("debug", mock_logger)

        # Check that it still works (function should uppercase it)
        self.assertEqual(keria.ogler.level, logging.DEBUG)
        mock_logger.setLevel.assert_called_with(logging.DEBUG)

    def test_truncated_formatter_imported(self):
        """Test that TruncatedFormatter is properly imported and used"""
        # Check that the handler has the correct formatter
        self.assertIsNotNone(keria.logHandler)
        self.assertIsNotNone(keria.formatter)
        from keria.monitoring.logs import TruncatedFormatter

        self.assertIsInstance(keria.formatter, TruncatedFormatter)

    def test_log_handler_configuration(self):
        """Test that log handler is properly configured"""
        self.assertIsNotNone(keria.logHandler)
        self.assertIsInstance(keria.logHandler, logging.StreamHandler)
        self.assertEqual(keria.logHandler.formatter, keria.formatter)


if __name__ == "__main__":
    unittest.main()

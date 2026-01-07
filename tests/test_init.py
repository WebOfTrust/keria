# -*- encoding: utf-8 -*-
"""
Test for keria.__init__
"""

import logging
import unittest
from unittest.mock import Mock
import keria


class TestKeriaInit(unittest.TestCase):
    def test_set_log_level_with_debug(self):
        mock_logger = Mock()
        keria.set_log_level("DEBUG", mock_logger)
        self.assertEqual(keria.ogler.level, logging.DEBUG)
        mock_logger.setLevel.assert_called_with(logging.DEBUG)


if __name__ == "__main__":
    unittest.main()

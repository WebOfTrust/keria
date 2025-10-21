# -*- encoding: utf-8 -*-
"""
main package
"""

__version__ = "0.2.0"  # also change in setup.py

import logging
from hio.help import ogling
from .monitoring.logs import TruncatedFormatter

log_name = "keria"  # name of this project that shows up in log messages
log_format_str = f"%(asctime)s [{log_name}] %(levelname)-8s %(module)s.%(funcName)s-%(lineno)s %(message)s"

ogler = ogling.initOgler(prefix=log_name, syslogged=False)
ogler.level = logging.INFO

formatter = TruncatedFormatter(log_format_str)
formatter.default_msec_format = None
logHandler = logging.StreamHandler()
logHandler.setFormatter(formatter)
ogler.baseFormatter = formatter
ogler.baseConsoleHandler = logHandler
ogler.baseConsoleHandler.setFormatter(formatter)
ogler.reopen(name=log_name, temp=True, clear=True)


def set_log_level(loglevel, logger):
    """Set the log level for the logger."""
    ogler.level = logging.getLevelName(loglevel.upper())
    logger.setLevel(ogler.level)

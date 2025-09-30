"""
Configure PyTest

Use this module to configure pytest
https://docs.pytest.org/en/latest/pythonpath.html

"""

import pytest

from keri.core import coring
from keri.help import helping
from keria.testing import testing_helper


@pytest.fixture
def helpers():
    return testing_helper.Helpers


@pytest.fixture
def seeder():
    return testing_helper.DbSeed


@pytest.fixture()
def mockHelpingNowUTC(monkeypatch):
    """
    Replace nowUTC universally with fixed value for testing
    """
    monkeypatch.setattr(helping, "nowUTC", testing_helper.Helpers.mockNowUTC)


@pytest.fixture()
def mockHelpingNowIso8601(monkeypatch):
    """
    Replace nowIso8601 universally with fixed value for testing
    """
    monkeypatch.setattr(helping, "nowIso8601", testing_helper.Helpers.mockNowIso8601)


@pytest.fixture()
def mockCoringRandomNonce(monkeypatch):
    """Replay randomNonce with fixed falue for testing"""
    monkeypatch.setattr(coring, "randomNonce", testing_helper.Helpers.mockRandomNonce)

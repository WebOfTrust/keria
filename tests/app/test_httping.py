# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.httping module

Testing the Mark II Agent
"""
from keria.core.httping import parseRangeHeader


def test_parse_range_header():
    # Test Defaults
    start, end = parseRangeHeader("", "agent")
    assert start == 0
    assert end == 9

    start, end = parseRangeHeader("", "agent", 8, 16)
    assert start == 8
    assert end == 16

    start, end = parseRangeHeader("identifier=9-20", "agent")
    assert start == 0
    assert end == 9

    # Test Valid range headers
    start, end = parseRangeHeader("agent=9-20", "agent")
    assert start == 9
    assert end == 20

    start, end = parseRangeHeader("agent=0-99", "agent")
    assert start == 0
    assert end == 99

    # Test edge cases
    start, end = parseRangeHeader("agent=0-", "agent")
    assert start == 0
    assert end == 9

    start, end = parseRangeHeader("agent=0-", "agent", end=100)
    assert start == 0
    assert end == 100

    start, end = parseRangeHeader("agent=-66", "agent")
    assert start == 0
    assert end == 66

    start, end = parseRangeHeader("agent=-55", "agent", start=45)
    assert start == 45
    assert end == 55

    # Test invalid values
    start, end = parseRangeHeader("agent=4-8-55", "agent", start=45, end=55)
    assert start == 45
    assert end == 55

    start, end = parseRangeHeader("agent=4-8-55", "agent")
    assert start == 0
    assert end == 9

    start, end = parseRangeHeader("agent=eight-55", "agent", start=45, end=55)
    assert start == 45
    assert end == 55

    start, end = parseRangeHeader("agent=4-banana", "agent")
    assert start == 0
    assert end == 9










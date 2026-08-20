"""tests/test_converter.py"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.converter import celsius_to_fahrenheit


def test_freezing_point():
    assert celsius_to_fahrenheit(0) == 32.0

def test_boiling_point():
    assert celsius_to_fahrenheit(100) == 212.0

def test_body_temp():
    assert abs(celsius_to_fahrenheit(37) - 98.6) < 0.1

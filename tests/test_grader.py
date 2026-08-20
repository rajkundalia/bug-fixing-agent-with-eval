"""tests/test_grader.py"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.grader import get_grade


def test_grade_a_at_boundary():
    assert get_grade(90) == "A"

def test_grade_a_above():
    assert get_grade(100) == "A"
    assert get_grade(95) == "A"

def test_grade_b():
    assert get_grade(85) == "B"

def test_grade_c():
    assert get_grade(75) == "C"

def test_grade_d():
    assert get_grade(65) == "D"

def test_grade_f():
    assert get_grade(50) == "F"

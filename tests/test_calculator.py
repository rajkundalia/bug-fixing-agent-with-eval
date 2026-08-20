"""tests/test_calculator.py"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from src.calculator import calculate_total, divide


# --- calculate_total ---

def test_calculate_total_normal():
    assert calculate_total([1, 2, 3]) == 6

def test_calculate_total_single():
    assert calculate_total([5]) == 5

def test_calculate_total_empty():
    assert calculate_total([]) == 0

def test_calculate_total_negatives():
    assert calculate_total([-1, -2, 3]) == 0


# --- divide ---

def test_divide_normal():
    assert divide(10, 2) == 5.0

def test_divide_by_zero_raises():
    with pytest.raises((ZeroDivisionError, ValueError)):
        divide(5, 0)

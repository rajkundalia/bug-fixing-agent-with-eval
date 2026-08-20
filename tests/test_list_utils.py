"""tests/test_list_utils.py"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from src.list_utils import flatten, remove_duplicates


# --- flatten ---

def test_flatten_normal():
    assert flatten([1, [2, 3], [4, [5]]]) == [1, 2, 3, 4, 5]

def test_flatten_empty():
    assert flatten([]) == []

def test_flatten_deeply_nested():
    deep = [0]
    for _ in range(200):
        deep = [deep]
    result = flatten(deep)
    assert result == [0]


# --- remove_duplicates ---

def test_remove_duplicates_order():
    assert remove_duplicates([3, 1, 2, 1, 3]) == [3, 1, 2]

def test_remove_duplicates_no_dupes():
    assert remove_duplicates([1, 2, 3]) == [1, 2, 3]

def test_remove_duplicates_empty():
    assert remove_duplicates([]) == []

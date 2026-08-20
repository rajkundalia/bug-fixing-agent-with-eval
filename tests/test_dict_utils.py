"""tests/test_dict_utils.py"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.dict_utils import merge_dicts


def test_merge_dicts_basic():
    result = merge_dicts({"a": 1}, {"b": 2})
    assert result == {"a": 1, "b": 2}

def test_merge_dicts_b_wins():
    result = merge_dicts({"a": 1}, {"a": 99})
    assert result["a"] == 99

def test_merge_dicts_does_not_mutate_a():
    a = {"x": 1}
    merge_dicts(a, {"y": 2})
    assert a == {"x": 1}, "merge_dicts mutated the first argument"

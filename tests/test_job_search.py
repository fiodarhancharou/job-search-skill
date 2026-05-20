# tests/test_job_search.py
import pytest
from pathlib import Path


def test_load_prompt_returns_string():
    from job_search import load_prompt
    result = load_prompt()
    assert isinstance(result, str)
    assert len(result) > 100


def test_load_prompt_contains_required_placeholders():
    from job_search import load_prompt
    result = load_prompt()
    assert "{job_details}" in result
    assert "{required_criteria}" in result
    assert "{preferred_criteria}" in result
    assert "{deal_breakers}" in result

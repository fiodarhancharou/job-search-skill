# tests/test_job_search.py
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


def test_load_config_returns_dict_with_required_keys():
    from job_search import load_config
    config = load_config()
    assert "profile" in config
    assert "required_criteria" in config
    assert "preferred_criteria" in config
    assert "deal_breakers" in config
    assert "search" in config


def test_load_config_profile_has_location():
    from job_search import load_config
    config = load_config()
    assert "location" in config["profile"]
    assert "salary_min_pln" in config["profile"]


def test_load_config_search_has_queries():
    from job_search import load_config
    config = load_config()
    assert len(config["search"]["queries"]) > 0
    assert config["search"]["max_results_per_query"] > 0

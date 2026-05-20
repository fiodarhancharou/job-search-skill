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


def test_job_listing_dataclass():
    from job_search import JobListing
    job = JobListing(
        title="Senior AI Engineer",
        company="Acme Corp",
        location="Remote, Poland",
        salary="25000 PLN",
        description="We build LLM-powered products.",
        url="https://linkedin.com/jobs/view/12345",
    )
    assert job.title == "Senior AI Engineer"
    assert job.url == "https://linkedin.com/jobs/view/12345"
    assert job.salary == "25000 PLN"


def test_evaluation_result_dataclass():
    from job_search import EvaluationResult, JobListing
    job = JobListing(
        title="Senior ML Engineer",
        company="Beta Inc",
        location="Krakow (hybrid)",
        salary="Not listed",
        description="ML platform role.",
        url="https://linkedin.com/jobs/view/99999",
    )
    result = EvaluationResult(
        job=job,
        tier="Strong Match",
        matched_required=["Python proficiency expected", "LLM/AI/ML focus"],
        matched_preferred=["RAG or agentic systems", "AWS or Azure cloud", "FastAPI"],
        deal_breakers_hit=[],
        reasoning="Matches all required and 3 preferred. No deal-breakers.",
    )
    assert result.tier == "Strong Match"
    assert len(result.matched_preferred) == 3
    assert result.deal_breakers_hit == []

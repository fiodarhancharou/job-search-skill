# tests/test_job_search.py
from pathlib import Path
from unittest.mock import MagicMock, patch
import json


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


def _make_api_response(tier: str, matched_required: list, matched_preferred: list, deal_breakers: list, reasoning: str):
    payload = json.dumps({
        "tier": tier,
        "matched_required": matched_required,
        "matched_preferred": matched_preferred,
        "deal_breakers_hit": deal_breakers,
        "reasoning": reasoning,
    })
    content_block = MagicMock()
    content_block.type = "text"
    content_block.text = payload
    response = MagicMock()
    response.content = [content_block]
    return response


def test_evaluate_job_strong_match():
    from job_search import evaluate_job, JobListing
    job = JobListing(
        title="Senior LLM Engineer",
        company="TechCo",
        location="Remote, Poland",
        salary="28000 PLN",
        description="Build RAG pipelines with Python, FastAPI, AWS. LLM focus, senior level, UoP contract available.",
        url="https://linkedin.com/jobs/view/1",
    )
    config = {
        "required_criteria": ["Python proficiency expected", "LLM/AI/ML focus (not generic backend)", "Senior level (5+ years implied or stated)"],
        "preferred_criteria": ["RAG or agentic systems experience valued", "AWS or Azure cloud", "FastAPI or backend Python stack", "Evaluation/observability tooling (Langfuse, MLflow, etc.)", "English-language team"],
        "deal_breakers": ["Requires relocation to office full-time", "B2B-only contract (no UoP option)"],
    }
    mock_response = _make_api_response(
        tier="Strong Match",
        matched_required=["Python proficiency expected", "LLM/AI/ML focus (not generic backend)", "Senior level (5+ years implied or stated)"],
        matched_preferred=["RAG or agentic systems experience valued", "AWS or Azure cloud", "FastAPI or backend Python stack"],
        deal_breakers=[],
        reasoning="Matches all required criteria. Three preferred criteria met, no deal-breakers.",
    )
    with patch("job_search.anthropic.Anthropic") as MockClient:
        mock_client = MagicMock()
        MockClient.return_value = mock_client
        mock_client.messages.create.return_value = mock_response

        result = evaluate_job(job, config, load_prompt_fn=lambda: "prompt {job_details} {required_criteria} {preferred_criteria} {deal_breakers}")

    assert result.tier == "Strong Match"
    assert len(result.matched_required) == 3
    assert len(result.matched_preferred) == 3
    assert result.deal_breakers_hit == []


def test_evaluate_job_skip_on_deal_breaker():
    from job_search import evaluate_job, JobListing
    job = JobListing(
        title="ML Engineer",
        company="CorpX",
        location="Warsaw (office only)",
        salary="20000 PLN",
        description="On-site required, B2B only.",
        url="https://linkedin.com/jobs/view/2",
    )
    config = {
        "required_criteria": ["Python proficiency expected"],
        "preferred_criteria": [],
        "deal_breakers": ["Requires relocation to office full-time", "B2B-only contract (no UoP option)"],
    }
    mock_response = _make_api_response(
        tier="Skip",
        matched_required=[],
        matched_preferred=[],
        deal_breakers=["Requires relocation to office full-time", "B2B-only contract (no UoP option)"],
        reasoning="Two deal-breakers hit. Immediate skip.",
    )
    with patch("job_search.anthropic.Anthropic") as MockClient:
        mock_client = MagicMock()
        MockClient.return_value = mock_client
        mock_client.messages.create.return_value = mock_response

        result = evaluate_job(job, config, load_prompt_fn=lambda: "prompt {job_details} {required_criteria} {preferred_criteria} {deal_breakers}")

    assert result.tier == "Skip"
    assert len(result.deal_breakers_hit) == 2


def _make_search_response(text_content: str, stop_reason: str = "end_turn"):
    content_block = MagicMock()
    content_block.type = "text"
    content_block.text = text_content
    response = MagicMock()
    response.stop_reason = stop_reason
    response.content = [content_block]
    return response


def test_search_linkedin_jobs_returns_list_of_job_listings():
    from job_search import search_linkedin_jobs, JobListing
    search_text = """
    Found these LinkedIn job listings:

    1. Senior AI Engineer at DataCo
    URL: https://www.linkedin.com/jobs/view/111
    Location: Remote, Poland
    Salary: 26000 PLN/month
    Description: Build AI pipelines with Python and LLMs. Senior role, UoP contract, remote-first team.

    2. Senior ML Engineer at MLStartup
    URL: https://www.linkedin.com/jobs/view/222
    Location: Krakow (hybrid)
    Salary: Not listed
    Description: ML research and deployment. RAG, agentic systems, AWS. English-speaking team.
    """
    mock_response = _make_search_response(search_text)

    with patch("job_search.anthropic.Anthropic") as MockClient:
        mock_client = MagicMock()
        MockClient.return_value = mock_client
        mock_client.messages.create.return_value = mock_response

        results = search_linkedin_jobs("Senior AI Engineer remote Poland LinkedIn", max_results=10)

    assert isinstance(results, list)
    assert len(results) >= 1
    assert all(isinstance(j, JobListing) for j in results)
    assert all(j.url.startswith("https://") for j in results)


def test_search_linkedin_jobs_handles_pause_turn():
    from job_search import search_linkedin_jobs
    pause_response = MagicMock()
    pause_response.stop_reason = "pause_turn"
    pause_response.content = []

    final_text = "1. Senior LLM Engineer at Acme\nURL: https://linkedin.com/jobs/view/333\nLocation: Remote\nSalary: 24000 PLN\nDescription: LLM work."
    final_response = _make_search_response(final_text)

    with patch("job_search.anthropic.Anthropic") as MockClient:
        mock_client = MagicMock()
        MockClient.return_value = mock_client
        mock_client.messages.create.side_effect = [pause_response, final_response]

        results = search_linkedin_jobs("Senior LLM Engineer hybrid Krakow", max_results=5)

    assert mock_client.messages.create.call_count == 2
    assert isinstance(results, list)

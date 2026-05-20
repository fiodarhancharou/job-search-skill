# Job Search Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a `/job-search` Claude Code skill that queries LinkedIn for Senior AI/ML Engineer roles via the Anthropic web_search tool, evaluates each listing against explicit YAML criteria, and writes a tiered markdown report.

**Architecture:** A Python script (`job_search.py`) reads criteria from `config.yaml`, calls the Claude API with the `web_search_20260209` server-side tool to discover job URLs, extracts details per listing, then calls Claude again (no tools) to evaluate each against a prompt template — returning structured JSON that the script sorts into Strong Match / Possible / Skip tiers in a dated report.

**Tech Stack:** Python 3.10+, `anthropic` SDK, `pyyaml`, `pathlib`, `datetime`, `json`, `dataclasses`, `pytest`

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `skills/job-search/SKILL.md` | Claude Code skill entrypoint |
| Create | `config.yaml` | User-editable search + evaluation criteria |
| Create | `prompts/evaluate_job.md` | Evaluation prompt template with scoring rubric |
| Create | `job_search.py` | Main pipeline: search → extract → evaluate → report |
| Create | `tests/test_job_search.py` | Unit tests for config loading, prompt loading, evaluation parsing, report generation |
| Create | `reports/` | Auto-created directory; one `.md` file per run |

---

## Task 1: Project Skeleton

**Files:**
- Create: `skills/job-search/SKILL.md`
- Create: `config.yaml`
- Create: `prompts/` (empty dir)
- Create: `reports/` (empty dir, gitkeep)
- Create: `tests/__init__.py`

- [ ] **Step 1: Create the SKILL.md entrypoint**

```markdown
---
name: job-search
description: Search LinkedIn for Senior AI/ML Engineer job listings matching your profile. Finds, evaluates, and ranks jobs into Strong Match / Possible / Skip. Run this when you want to find new job opportunities.
---

Run the job search pipeline:

```bash
cd /Users/Fiodar_Hancharou/Desktop/work/personal/eval_example
python job_search.py
```

The script reads `config.yaml` for all search queries and evaluation criteria, then writes a ranked report to `reports/job-search-YYYY-MM-DD.md`.
```

Save to: `eval_example/skills/job-search/SKILL.md`

- [ ] **Step 2: Create config.yaml**

```yaml
profile:
  target_roles:
    - "Senior AI Engineer"
    - "Senior ML Engineer"
    - "Senior LLM Engineer"
    - "AI Tech Lead"
  location: "remote or hybrid Krakow Poland"
  salary_min_pln: 24000
  contract_type: "UoP"

required_criteria:
  - Python proficiency expected
  - LLM/AI/ML focus (not generic backend)
  - Senior level (5+ years implied or stated)

preferred_criteria:
  - RAG or agentic systems experience valued
  - AWS or Azure cloud
  - FastAPI or backend Python stack
  - Evaluation/observability tooling (Langfuse, MLflow, etc.)
  - English-language team

deal_breakers:
  - Requires relocation to office full-time
  - Requires security clearance
  - Junior or mid-level role disguised as senior
  - Non-AI/ML role (pure backend, DevOps, data analyst, etc.)
  - B2B-only contract (no UoP option)

search:
  queries:
    - "Senior AI Engineer remote Poland LinkedIn"
    - "Senior LLM Engineer hybrid Krakow"
    - "Senior ML Engineer RAG agentic remote Europe"
  max_results_per_query: 10
```

Save to: `eval_example/config.yaml`

- [ ] **Step 3: Create directory structure**

```bash
mkdir -p eval_example/skills/job-search
mkdir -p eval_example/prompts
mkdir -p eval_example/reports
mkdir -p eval_example/tests
touch eval_example/reports/.gitkeep
touch eval_example/tests/__init__.py
```

- [ ] **Step 4: Verify structure**

```bash
find eval_example -type f | sort
```

Expected output includes:
```
eval_example/config.yaml
eval_example/skills/job-search/SKILL.md
eval_example/reports/.gitkeep
eval_example/tests/__init__.py
```

- [ ] **Step 5: Commit**

```bash
git add eval_example/config.yaml eval_example/skills/ eval_example/reports/.gitkeep eval_example/tests/__init__.py
git commit -m "feat: add job-search skill skeleton and config"
```

---

## Task 2: Evaluation Prompt Template

**Files:**
- Create: `prompts/evaluate_job.md`

- [ ] **Step 1: Write the failing test**

```python
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
```

Save to: `eval_example/tests/test_job_search.py`

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/Fiodar_Hancharou/Desktop/work/personal/eval_example
python -m pytest tests/test_job_search.py::test_load_prompt_returns_string tests/test_job_search.py::test_load_prompt_contains_required_placeholders -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'job_search'`

- [ ] **Step 3: Create the prompt template**

```markdown
You are a job evaluator for a Senior AI/ML Engineer candidate based in Poland.

## Job Listing to Evaluate

{job_details}

## Evaluation Criteria

### Required (all must be met to avoid Skip tier):
{required_criteria}

### Preferred (count of met criteria determines Strong Match vs Possible):
{preferred_criteria}

### Deal-Breakers (any single hit → Skip tier immediately):
{deal_breakers}

## Tiering Rules

- **Strong Match**: zero deal-breakers hit AND all required criteria met AND 3 or more preferred criteria met
- **Possible**: zero deal-breakers hit AND all required criteria met AND fewer than 3 preferred criteria met
- **Skip**: any deal-breaker hit OR any required criterion not met

## Instructions

Evaluate the job listing above strictly against the criteria. Be conservative — if a criterion is ambiguous or not clearly stated, treat it as not met.

Respond with valid JSON only, no markdown fences, no extra text:

{{
  "tier": "Strong Match" | "Possible" | "Skip",
  "matched_required": ["list of required criteria that are met"],
  "matched_preferred": ["list of preferred criteria that are met"],
  "deal_breakers_hit": ["list of deal-breakers that apply"],
  "reasoning": "Two sentences explaining the tier decision."
}}
```

Save to: `eval_example/prompts/evaluate_job.md`

- [ ] **Step 4: Create minimal job_search.py with load_prompt()**

```python
# job_search.py
from pathlib import Path


def load_prompt() -> str:
    prompt_path = Path(__file__).parent / "prompts" / "evaluate_job.md"
    return prompt_path.read_text(encoding="utf-8")
```

Save to: `eval_example/job_search.py`

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd /Users/Fiodar_Hancharou/Desktop/work/personal/eval_example
python -m pytest tests/test_job_search.py::test_load_prompt_returns_string tests/test_job_search.py::test_load_prompt_contains_required_placeholders -v
```

Expected: PASS (2 tests)

- [ ] **Step 6: Commit**

```bash
git add eval_example/prompts/evaluate_job.md eval_example/job_search.py eval_example/tests/test_job_search.py
git commit -m "feat: add evaluation prompt template and load_prompt()"
```

---

## Task 3: Config Loading

**Files:**
- Modify: `job_search.py` — add `load_config()` and `Config` dataclass
- Modify: `tests/test_job_search.py` — add config tests

- [ ] **Step 1: Write the failing tests**

Append to `eval_example/tests/test_job_search.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/Fiodar_Hancharou/Desktop/work/personal/eval_example
python -m pytest tests/test_job_search.py::test_load_config_returns_dict_with_required_keys -v
```

Expected: FAIL with `ImportError` — `load_config` not defined

- [ ] **Step 3: Add load_config() to job_search.py**

Replace the contents of `eval_example/job_search.py` with:

```python
# job_search.py
from pathlib import Path
import yaml


def load_config() -> dict:
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_prompt() -> str:
    prompt_path = Path(__file__).parent / "prompts" / "evaluate_job.md"
    return prompt_path.read_text(encoding="utf-8")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /Users/Fiodar_Hancharou/Desktop/work/personal/eval_example
python -m pytest tests/test_job_search.py -v
```

Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add eval_example/job_search.py eval_example/tests/test_job_search.py
git commit -m "feat: add load_config() with yaml parsing"
```

---

## Task 4: Data Models

**Files:**
- Modify: `job_search.py` — add `JobListing` and `EvaluationResult` dataclasses
- Modify: `tests/test_job_search.py` — add dataclass tests

- [ ] **Step 1: Write the failing tests**

Append to `eval_example/tests/test_job_search.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/Fiodar_Hancharou/Desktop/work/personal/eval_example
python -m pytest tests/test_job_search.py::test_job_listing_dataclass tests/test_job_search.py::test_evaluation_result_dataclass -v
```

Expected: FAIL with `ImportError` — `JobListing` not defined

- [ ] **Step 3: Add dataclasses to job_search.py**

Replace the contents of `eval_example/job_search.py` with:

```python
# job_search.py
from dataclasses import dataclass, field
from pathlib import Path
import yaml


@dataclass
class JobListing:
    title: str
    company: str
    location: str
    salary: str
    description: str
    url: str


@dataclass
class EvaluationResult:
    job: JobListing
    tier: str  # "Strong Match" | "Possible" | "Skip"
    matched_required: list[str] = field(default_factory=list)
    matched_preferred: list[str] = field(default_factory=list)
    deal_breakers_hit: list[str] = field(default_factory=list)
    reasoning: str = ""


def load_config() -> dict:
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_prompt() -> str:
    prompt_path = Path(__file__).parent / "prompts" / "evaluate_job.md"
    return prompt_path.read_text(encoding="utf-8")
```

- [ ] **Step 4: Run all tests to verify they pass**

```bash
cd /Users/Fiodar_Hancharou/Desktop/work/personal/eval_example
python -m pytest tests/test_job_search.py -v
```

Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add eval_example/job_search.py eval_example/tests/test_job_search.py
git commit -m "feat: add JobListing and EvaluationResult dataclasses"
```

---

## Task 5: Job Evaluation Function

**Files:**
- Modify: `job_search.py` — add `evaluate_job()`
- Modify: `tests/test_job_search.py` — add evaluation tests (with mocked API)

- [ ] **Step 1: Write the failing tests**

Append to `eval_example/tests/test_job_search.py`:

```python
from unittest.mock import MagicMock, patch
import json


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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/Fiodar_Hancharou/Desktop/work/personal/eval_example
python -m pytest tests/test_job_search.py::test_evaluate_job_strong_match tests/test_job_search.py::test_evaluate_job_skip_on_deal_breaker -v
```

Expected: FAIL with `ImportError` — `evaluate_job` not defined

- [ ] **Step 3: Implement evaluate_job() in job_search.py**

Append to `eval_example/job_search.py` (below the existing functions):

```python
import anthropic
import json


def evaluate_job(
    job: JobListing,
    config: dict,
    load_prompt_fn=None,
) -> EvaluationResult:
    if load_prompt_fn is None:
        load_prompt_fn = load_prompt

    prompt_template = load_prompt_fn()
    job_details = (
        f"Title: {job.title}\n"
        f"Company: {job.company}\n"
        f"Location: {job.location}\n"
        f"Salary: {job.salary}\n"
        f"URL: {job.url}\n\n"
        f"Description:\n{job.description}"
    )
    required_list = "\n".join(f"- {c}" for c in config["required_criteria"])
    preferred_list = "\n".join(f"- {c}" for c in config["preferred_criteria"])
    deal_breakers_list = "\n".join(f"- {c}" for c in config["deal_breakers"])

    prompt = prompt_template.format(
        job_details=job_details,
        required_criteria=required_list,
        preferred_criteria=preferred_list,
        deal_breakers=deal_breakers_list,
    )

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    text = next(b.text for b in response.content if b.type == "text")
    data = json.loads(text)

    return EvaluationResult(
        job=job,
        tier=data["tier"],
        matched_required=data.get("matched_required", []),
        matched_preferred=data.get("matched_preferred", []),
        deal_breakers_hit=data.get("deal_breakers_hit", []),
        reasoning=data.get("reasoning", ""),
    )
```

The full `eval_example/job_search.py` now contains all imports at the top. Move the `import anthropic` and `import json` lines to the top of the file:

```python
# job_search.py
import anthropic
import json
from dataclasses import dataclass, field
from pathlib import Path
import yaml


@dataclass
class JobListing:
    title: str
    company: str
    location: str
    salary: str
    description: str
    url: str


@dataclass
class EvaluationResult:
    job: JobListing
    tier: str  # "Strong Match" | "Possible" | "Skip"
    matched_required: list[str] = field(default_factory=list)
    matched_preferred: list[str] = field(default_factory=list)
    deal_breakers_hit: list[str] = field(default_factory=list)
    reasoning: str = ""


def load_config() -> dict:
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_prompt() -> str:
    prompt_path = Path(__file__).parent / "prompts" / "evaluate_job.md"
    return prompt_path.read_text(encoding="utf-8")


def evaluate_job(
    job: JobListing,
    config: dict,
    load_prompt_fn=None,
) -> EvaluationResult:
    if load_prompt_fn is None:
        load_prompt_fn = load_prompt

    prompt_template = load_prompt_fn()
    job_details = (
        f"Title: {job.title}\n"
        f"Company: {job.company}\n"
        f"Location: {job.location}\n"
        f"Salary: {job.salary}\n"
        f"URL: {job.url}\n\n"
        f"Description:\n{job.description}"
    )
    required_list = "\n".join(f"- {c}" for c in config["required_criteria"])
    preferred_list = "\n".join(f"- {c}" for c in config["preferred_criteria"])
    deal_breakers_list = "\n".join(f"- {c}" for c in config["deal_breakers"])

    prompt = prompt_template.format(
        job_details=job_details,
        required_criteria=required_list,
        preferred_criteria=preferred_list,
        deal_breakers=deal_breakers_list,
    )

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    text = next(b.text for b in response.content if b.type == "text")
    data = json.loads(text)

    return EvaluationResult(
        job=job,
        tier=data["tier"],
        matched_required=data.get("matched_required", []),
        matched_preferred=data.get("matched_preferred", []),
        deal_breakers_hit=data.get("deal_breakers_hit", []),
        reasoning=data.get("reasoning", ""),
    )
```

- [ ] **Step 4: Run all tests to verify they pass**

```bash
cd /Users/Fiodar_Hancharou/Desktop/work/personal/eval_example
python -m pytest tests/test_job_search.py -v
```

Expected: PASS (9 tests)

- [ ] **Step 5: Commit**

```bash
git add eval_example/job_search.py eval_example/tests/test_job_search.py
git commit -m "feat: add evaluate_job() with Claude API call and JSON parsing"
```

---

## Task 6: LinkedIn Search Function

**Files:**
- Modify: `job_search.py` — add `search_linkedin_jobs()`
- Modify: `tests/test_job_search.py` — add search tests (with mocked API)

- [ ] **Step 1: Write the failing tests**

Append to `eval_example/tests/test_job_search.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/Fiodar_Hancharou/Desktop/work/personal/eval_example
python -m pytest tests/test_job_search.py::test_search_linkedin_jobs_returns_list_of_job_listings tests/test_job_search.py::test_search_linkedin_jobs_handles_pause_turn -v
```

Expected: FAIL with `ImportError` — `search_linkedin_jobs` not defined

- [ ] **Step 3: Implement search_linkedin_jobs() in job_search.py**

Append to `eval_example/job_search.py`:

```python
import re


def _parse_job_listings_from_text(text: str) -> list[JobListing]:
    listings = []
    url_pattern = re.compile(r"https?://(?:www\.)?linkedin\.com/jobs/view/\S+")
    blocks = re.split(r"\n\s*\n", text.strip())

    for block in blocks:
        urls = url_pattern.findall(block)
        if not urls:
            continue
        url = urls[0].rstrip(".,)")
        lines = [l.strip() for l in block.strip().splitlines() if l.strip()]

        title = "Unknown Title"
        company = "Unknown Company"
        location = "Not listed"
        salary = "Not listed"
        desc_lines = []

        for line in lines:
            low = line.lower()
            if low.startswith("url:") or "linkedin.com/jobs" in low:
                continue
            elif low.startswith("location:"):
                location = line.split(":", 1)[1].strip()
            elif low.startswith("salary:"):
                salary = line.split(":", 1)[1].strip()
            elif low.startswith("description:"):
                desc_lines.append(line.split(":", 1)[1].strip())
            elif " at " in line and not title:
                parts = line.split(" at ", 1)
                title = re.sub(r"^\d+\.\s*", "", parts[0]).strip()
                company = parts[1].strip()
            else:
                desc_lines.append(line)

        description = " ".join(desc_lines) if desc_lines else "No description extracted."
        listings.append(JobListing(
            title=title,
            company=company,
            location=location,
            salary=salary,
            description=description,
            url=url,
        ))

    return listings


def search_linkedin_jobs(query: str, max_results: int = 10) -> list[JobListing]:
    client = anthropic.Anthropic()
    messages = [
        {
            "role": "user",
            "content": (
                f"Search LinkedIn for job listings matching this query: '{query}'. "
                f"Find up to {max_results} real job postings. "
                "For each listing return: the job title, company name, location, salary (or 'Not listed'), "
                "a brief description of the role and requirements, and the full LinkedIn job URL. "
                "Format each listing as:\n"
                "N. [Title] at [Company]\n"
                "URL: [linkedin url]\n"
                "Location: [location]\n"
                "Salary: [salary or Not listed]\n"
                "Description: [brief description]\n"
            ),
        }
    ]

    while True:
        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=4096,
            tools=[{"type": "web_search_20260209", "name": "web_search"}],
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            text_blocks = [b.text for b in response.content if b.type == "text"]
            full_text = "\n\n".join(text_blocks)
            return _parse_job_listings_from_text(full_text)

        if response.stop_reason == "pause_turn":
            messages = messages + [
                {"role": "assistant", "content": response.content},
                {"role": "user", "content": "Please continue."},
            ]
            continue

        text_blocks = [b.text for b in response.content if b.type == "text"]
        full_text = "\n\n".join(text_blocks)
        return _parse_job_listings_from_text(full_text)
```

Also add `import re` at the top of the file alongside existing imports.

- [ ] **Step 4: Run all tests**

```bash
cd /Users/Fiodar_Hancharou/Desktop/work/personal/eval_example
python -m pytest tests/test_job_search.py -v
```

Expected: PASS (11 tests)

- [ ] **Step 5: Commit**

```bash
git add eval_example/job_search.py eval_example/tests/test_job_search.py
git commit -m "feat: add search_linkedin_jobs() with pause_turn handling and listing parser"
```

---

## Task 7: Report Generator

**Files:**
- Modify: `job_search.py` — add `generate_report()`
- Modify: `tests/test_job_search.py` — add report tests

- [ ] **Step 1: Write the failing tests**

Append to `eval_example/tests/test_job_search.py`:

```python
from datetime import date


def _make_evaluation_result(tier: str, title: str = "Senior AI Eng", company: str = "Acme") -> "EvaluationResult":
    from job_search import EvaluationResult, JobListing
    job = JobListing(
        title=title, company=company, location="Remote", salary="25000 PLN",
        description="AI role.", url=f"https://linkedin.com/jobs/view/{hash(title) % 9999}",
    )
    return EvaluationResult(
        job=job,
        tier=tier,
        matched_required=["Python proficiency expected", "LLM/AI/ML focus"],
        matched_preferred=["RAG or agentic systems"] if tier != "Skip" else [],
        deal_breakers_hit=["B2B-only contract"] if tier == "Skip" else [],
        reasoning="Test reasoning sentence one. Test reasoning sentence two.",
    )


def test_generate_report_creates_file(tmp_path):
    from job_search import generate_report, EvaluationResult
    results = [
        _make_evaluation_result("Strong Match", "LLM Lead", "BigCo"),
        _make_evaluation_result("Possible", "ML Engineer", "SmallCo"),
        _make_evaluation_result("Skip", "Data Analyst", "BadCo"),
    ]
    run_date = date(2026, 5, 20)
    report_path = generate_report(results, reports_dir=tmp_path, run_date=run_date)
    assert report_path.exists()
    assert report_path.name == "job-search-2026-05-20.md"


def test_generate_report_content_structure(tmp_path):
    from job_search import generate_report
    results = [
        _make_evaluation_result("Strong Match", "LLM Lead", "BigCo"),
        _make_evaluation_result("Possible", "ML Engineer", "SmallCo"),
        _make_evaluation_result("Skip", "Data Analyst", "BadCo"),
    ]
    run_date = date(2026, 5, 20)
    report_path = generate_report(results, reports_dir=tmp_path, run_date=run_date)
    content = report_path.read_text(encoding="utf-8")

    assert "# Job Search Report" in content
    assert "## Summary" in content
    assert "Strong Match: 1" in content
    assert "Possible: 1" in content
    assert "Skip: 1" in content
    assert "## Strong Match" in content
    assert "## Possible" in content
    assert "## Skip" in content
    assert "LLM Lead" in content
    assert "ML Engineer" in content
    assert "Data Analyst" in content
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/Fiodar_Hancharou/Desktop/work/personal/eval_example
python -m pytest tests/test_job_search.py::test_generate_report_creates_file tests/test_job_search.py::test_generate_report_content_structure -v
```

Expected: FAIL with `ImportError` — `generate_report` not defined

- [ ] **Step 3: Implement generate_report() in job_search.py**

Add `from datetime import date` to imports at top, then append to `eval_example/job_search.py`:

```python
from datetime import date as date_type


def generate_report(
    results: list[EvaluationResult],
    reports_dir: Path = None,
    run_date=None,
) -> Path:
    if reports_dir is None:
        reports_dir = Path(__file__).parent / "reports"
    reports_dir = Path(reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)

    if run_date is None:
        from datetime import date
        run_date = date.today()

    filename = f"job-search-{run_date.strftime('%Y-%m-%d')}.md"
    report_path = reports_dir / filename

    strong = [r for r in results if r.tier == "Strong Match"]
    possible = [r for r in results if r.tier == "Possible"]
    skip = [r for r in results if r.tier == "Skip"]

    lines = [
        f"# Job Search Report — {run_date.strftime('%Y-%m-%d')}",
        "",
        "## Summary",
        f"- Evaluated: {len(results)} listings",
        f"- Strong Match: {len(strong)} | Possible: {len(possible)} | Skip: {len(skip)}",
        "",
        "---",
    ]

    def render_section(section_results: list[EvaluationResult], heading: str) -> list[str]:
        out = ["", f"## {heading}", ""]
        if not section_results:
            out.append("_None_")
            return out
        for i, r in enumerate(section_results, 1):
            out += [
                f"### {i}. {r.job.title} — {r.job.company}",
                f"- **URL**: {r.job.url}",
                f"- **Location**: {r.job.location}",
                f"- **Salary**: {r.job.salary}",
                f"- **Matched required**: {', '.join(r.matched_required) or 'None'}",
                f"- **Matched preferred**: {', '.join(r.matched_preferred) or 'None'}",
            ]
            if r.deal_breakers_hit:
                out.append(f"- **Deal-breakers hit**: {', '.join(r.deal_breakers_hit)}")
            out += [f"- **Why**: {r.reasoning}", ""]
        return out

    lines += render_section(strong, "Strong Match")
    lines += render_section(possible, "Possible")
    lines += render_section(skip, "Skip")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path
```

- [ ] **Step 4: Run all tests**

```bash
cd /Users/Fiodar_Hancharou/Desktop/work/personal/eval_example
python -m pytest tests/test_job_search.py -v
```

Expected: PASS (13 tests)

- [ ] **Step 5: Commit**

```bash
git add eval_example/job_search.py eval_example/tests/test_job_search.py
git commit -m "feat: add generate_report() producing dated markdown report"
```

---

## Task 8: Main Pipeline

**Files:**
- Modify: `job_search.py` — add `main()` entry point
- Modify: `tests/test_job_search.py` — add integration smoke test

- [ ] **Step 1: Write the failing test**

Append to `eval_example/tests/test_job_search.py`:

```python
def test_main_produces_report_file(tmp_path):
    from job_search import main, JobListing, EvaluationResult

    fake_jobs = [
        JobListing("Senior AI Engineer", "TechCo", "Remote", "26000 PLN", "LLM role.", "https://linkedin.com/jobs/view/1"),
    ]
    fake_eval = EvaluationResult(
        job=fake_jobs[0],
        tier="Strong Match",
        matched_required=["Python proficiency expected", "LLM/AI/ML focus (not generic backend)", "Senior level (5+ years implied or stated)"],
        matched_preferred=["RAG or agentic systems experience valued", "AWS or Azure cloud", "FastAPI or backend Python stack"],
        deal_breakers_hit=[],
        reasoning="All required met, three preferred met.",
    )

    with patch("job_search.search_linkedin_jobs", return_value=fake_jobs) as mock_search, \
         patch("job_search.evaluate_job", return_value=fake_eval) as mock_eval:
        report_path = main(reports_dir=tmp_path)

    assert report_path.exists()
    assert mock_search.call_count >= 1
    assert mock_eval.call_count >= 1
    content = report_path.read_text()
    assert "Strong Match" in content
    assert "TechCo" in content
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/Fiodar_Hancharou/Desktop/work/personal/eval_example
python -m pytest tests/test_job_search.py::test_main_produces_report_file -v
```

Expected: FAIL with `ImportError` — `main` not defined or signature mismatch

- [ ] **Step 3: Implement main() in job_search.py**

Append to `eval_example/job_search.py`:

```python
def main(reports_dir: Path = None) -> Path:
    config = load_config()
    queries = config["search"]["queries"]
    max_per_query = config["search"]["max_results_per_query"]

    all_jobs: list[JobListing] = []
    for query in queries:
        print(f"Searching: {query}")
        jobs = search_linkedin_jobs(query, max_results=max_per_query)
        print(f"  Found {len(jobs)} listings")
        all_jobs.extend(jobs)

    seen_urls: set[str] = set()
    unique_jobs = []
    for job in all_jobs:
        if job.url not in seen_urls:
            seen_urls.add(job.url)
            unique_jobs.append(job)

    print(f"\nEvaluating {len(unique_jobs)} unique listings...")
    results: list[EvaluationResult] = []
    for job in unique_jobs:
        print(f"  Evaluating: {job.title} at {job.company}")
        result = evaluate_job(job, config)
        results.append(result)

    report_path = generate_report(results, reports_dir=reports_dir)
    strong = sum(1 for r in results if r.tier == "Strong Match")
    possible = sum(1 for r in results if r.tier == "Possible")
    skip = sum(1 for r in results if r.tier == "Skip")
    print(f"\nReport written to: {report_path}")
    print(f"Strong Match: {strong} | Possible: {possible} | Skip: {skip}")
    return report_path


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run all tests**

```bash
cd /Users/Fiodar_Hancharou/Desktop/work/personal/eval_example
python -m pytest tests/test_job_search.py -v
```

Expected: PASS (14 tests)

- [ ] **Step 5: Commit**

```bash
git add eval_example/job_search.py eval_example/tests/test_job_search.py
git commit -m "feat: add main() pipeline — search, deduplicate, evaluate, report"
```

---

## Task 9: Dependency Setup & Smoke Run

**Files:**
- Create: `requirements.txt`

- [ ] **Step 1: Create requirements.txt**

```
anthropic>=0.52.0
pyyaml>=6.0
pytest>=8.0
```

Save to: `eval_example/requirements.txt`

- [ ] **Step 2: Install dependencies**

```bash
cd /Users/Fiodar_Hancharou/Desktop/work/personal/eval_example
pip install -r requirements.txt
```

Expected: Packages installed without errors. Verify with:

```bash
python -c "import anthropic, yaml; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Run full test suite**

```bash
cd /Users/Fiodar_Hancharou/Desktop/work/personal/eval_example
python -m pytest tests/test_job_search.py -v
```

Expected: PASS (14 tests), no failures

- [ ] **Step 4: Verify ANTHROPIC_API_KEY is set**

```bash
python -c "import os; print('Key set:', bool(os.environ.get('ANTHROPIC_API_KEY')))"
```

Expected: `Key set: True`

If False, set it: `export ANTHROPIC_API_KEY=your_key_here`

- [ ] **Step 5: Dry-run the script (one query, verify it starts)**

```bash
cd /Users/Fiodar_Hancharou/Desktop/work/personal/eval_example
python -c "
from job_search import load_config, load_prompt
config = load_config()
prompt = load_prompt()
print('Config loaded OK. Queries:', config['search']['queries'])
print('Prompt loaded OK. Length:', len(prompt))
"
```

Expected output:
```
Config loaded OK. Queries: ['Senior AI Engineer remote Poland LinkedIn', ...]
Prompt loaded OK. Length: [>100]
```

- [ ] **Step 6: Commit**

```bash
git add eval_example/requirements.txt
git commit -m "chore: add requirements.txt for anthropic, pyyaml, pytest"
```

---

## Task 10: End-to-End Verification

- [ ] **Step 1: Run the full pipeline once**

```bash
cd /Users/Fiodar_Hancharou/Desktop/work/personal/eval_example
python job_search.py
```

Expected output:
```
Searching: Senior AI Engineer remote Poland LinkedIn
  Found N listings
Searching: Senior LLM Engineer hybrid Krakow
  Found N listings
...
Evaluating N unique listings...
  Evaluating: [title] at [company]
  ...
Report written to: reports/job-search-2026-05-20.md
Strong Match: N | Possible: N | Skip: N
```

- [ ] **Step 2: Verify report file exists and is readable**

```bash
ls -lh /Users/Fiodar_Hancharou/Desktop/work/personal/eval_example/reports/
```

Expected: `job-search-2026-05-20.md` exists with non-zero size

- [ ] **Step 3: Check report structure**

```bash
head -30 /Users/Fiodar_Hancharou/Desktop/work/personal/eval_example/reports/job-search-2026-05-20.md
```

Expected: Shows `# Job Search Report`, `## Summary`, tier counts

- [ ] **Step 4: Commit report as example output (optional)**

```bash
git add eval_example/reports/job-search-2026-05-20.md
git commit -m "docs: add example job search report from first run"
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] `SKILL.md` — Task 1
- [x] `config.yaml` — Task 1
- [x] `prompts/evaluate_job.md` — Task 2
- [x] `job_search.py` with all named functions — Tasks 3–8
- [x] Tiering logic (Strong Match/Possible/Skip) — Task 2 prompt + Task 5 tests
- [x] Report format per spec — Task 7
- [x] Web search with pause_turn loop — Task 6
- [x] Deduplication across queries — Task 8

**No placeholders:** All code blocks are complete implementations.

**Type consistency:** `JobListing`, `EvaluationResult`, `load_config()`, `load_prompt()`, `evaluate_job()`, `search_linkedin_jobs()`, `generate_report()`, `main()` — all consistent across tasks.

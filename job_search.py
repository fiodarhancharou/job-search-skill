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

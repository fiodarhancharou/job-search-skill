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

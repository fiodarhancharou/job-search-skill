# job_search.py
from pathlib import Path


def load_prompt() -> str:
    prompt_path = Path(__file__).parent / "prompts" / "evaluate_job.md"
    return prompt_path.read_text(encoding="utf-8")

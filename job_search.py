# job_search.py
import json
import re
import subprocess
from dataclasses import dataclass, field
from datetime import date as date_type
from pathlib import Path
import yaml

_LINKEDIN_URL_PATTERN = re.compile(r"https?://(?:www\.)?linkedin\.com/jobs/view/\S+")


_EVAL_JSON_SCHEMA = json.dumps({
    "type": "object",
    "properties": {
        "tier": {"type": "string", "enum": ["Strong Match", "Possible", "Skip"]},
        "matched_required": {"type": "array", "items": {"type": "string"}},
        "matched_preferred": {"type": "array", "items": {"type": "string"}},
        "deal_breakers_hit": {"type": "array", "items": {"type": "string"}},
        "reasoning": {"type": "string"},
    },
    "required": ["tier", "matched_required", "matched_preferred", "deal_breakers_hit", "reasoning"],
})


def _claude_cli(prompt: str, tools: list[str] | None = None, json_schema: str | None = None) -> str:
    print(f"    [claude] calling CLI…")
    cmd = ["claude", "-p", prompt]
    if tools:
        cmd += ["--allowedTools"] + tools
    if json_schema:
        cmd += ["--json-schema", json_schema, "--output-format", "json"]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if result.returncode != 0:
        raise RuntimeError(f"claude CLI error: {result.stderr.strip()}")
    output = result.stdout.strip()
    if json_schema:
        parsed = json.loads(output)
        return json.dumps(parsed["structured_output"])
    print(f"    [claude] got {len(output)} chars")
    return output


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

    text = _claude_cli(prompt, json_schema=_EVAL_JSON_SCHEMA)
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[-1]
        stripped = stripped.rsplit("```", 1)[0].strip()
    try:
        data = json.loads(stripped)
    except json.JSONDecodeError as e:
        raise ValueError(f"Evaluation response was not valid JSON for {job.url}: {e}\nResponse: {text[:200]}") from e
    print(f"    → {data['tier']} | required={len(data.get('matched_required', []))} | preferred={len(data.get('matched_preferred', []))} | deal-breakers={len(data.get('deal_breakers_hit', []))}")

    return EvaluationResult(
        job=job,
        tier=data["tier"],
        matched_required=data.get("matched_required", []),
        matched_preferred=data.get("matched_preferred", []),
        deal_breakers_hit=data.get("deal_breakers_hit", []),
        reasoning=data.get("reasoning", ""),
    )


def _parse_job_listings_from_text(text: str) -> list[JobListing]:
    listings = []
    blocks = re.split(r"\n\s*\n", text.strip())

    for block in blocks:
        urls = _LINKEDIN_URL_PATTERN.findall(block)
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
            elif " at " in line and title == "Unknown Title":
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
    prompt = (
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
    )
    full_text = _claude_cli(prompt, tools=["WebSearch"])
    listings = _parse_job_listings_from_text(full_text)
    print(f"    parsed {len(listings)} listings from response")
    return listings


def generate_report(
    results: list[EvaluationResult],
    reports_dir=None,
    run_date=None,
    searched_queries: int = 0,
    found_count: int = 0,
) -> Path:
    if reports_dir is None:
        reports_dir = Path(__file__).parent / "reports"
    reports_dir = Path(reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)

    if run_date is None:
        run_date = date_type.today()

    filename = f"job-search-{run_date.strftime('%Y-%m-%d')}.md"
    report_path = reports_dir / filename

    strong = [r for r in results if r.tier == "Strong Match"]
    possible = [r for r in results if r.tier == "Possible"]
    skip = [r for r in results if r.tier == "Skip"]

    lines = [
        f"# Job Search Report — {run_date.strftime('%Y-%m-%d')}",
        "",
        "## Summary",
        f"- Searched: {searched_queries} queries | Found: {found_count} listings | Evaluated: {len(results)}",
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


def _cache_path(base_dir: Path = None) -> Path:
    base = Path(base_dir) if base_dir else Path(__file__).parent / "cache"
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{date_type.today().strftime('%Y-%m-%d')}.json"


def _load_cache(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"searches": {}, "evaluations": {}}


def _save_cache(path: Path, cache: dict) -> None:
    path.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")


def _job_to_dict(job: JobListing) -> dict:
    return {"title": job.title, "company": job.company, "location": job.location,
            "salary": job.salary, "description": job.description, "url": job.url}


def _job_from_dict(d: dict) -> JobListing:
    return JobListing(**d)


def _eval_to_dict(r: EvaluationResult) -> dict:
    return {"tier": r.tier, "matched_required": r.matched_required,
            "matched_preferred": r.matched_preferred, "deal_breakers_hit": r.deal_breakers_hit,
            "reasoning": r.reasoning}


def main(reports_dir=None, cache_dir=None) -> Path:
    config = load_config()
    queries = config["search"]["queries"]
    max_per_query = config["search"]["max_results_per_query"]

    cache_file = _cache_path(cache_dir)
    cache = _load_cache(cache_file)
    cached_searches = sum(1 for q in queries if q in cache["searches"])
    print(f"Runner: claude CLI")
    print(f"Cache: {cache_file} ({cached_searches}/{len(queries)} queries cached, {len(cache['evaluations'])} evaluations cached)")
    print()

    all_jobs: list[JobListing] = []
    for query in queries:
        if query in cache["searches"]:
            jobs = [_job_from_dict(d) for d in cache["searches"][query]]
            print(f"Searching: {query} (cached, {len(jobs)} listings)")
        else:
            print(f"Searching: {query}")
            jobs = search_linkedin_jobs(query, max_results=max_per_query)
            cache["searches"][query] = [_job_to_dict(j) for j in jobs]
            _save_cache(cache_file, cache)
            print(f"  Found {len(jobs)} listings")
        all_jobs.extend(jobs)

    seen_urls: set[str] = set()
    unique_jobs = []
    for job in all_jobs:
        if job.url not in seen_urls:
            seen_urls.add(job.url)
            unique_jobs.append(job)

    print(f"\n{len(unique_jobs)} unique listings after deduplication ({len(all_jobs) - len(unique_jobs)} duplicates removed)")
    print(f"\nEvaluating {len(unique_jobs)} unique listings...")
    results: list[EvaluationResult] = []
    for job in unique_jobs:
        if job.url in cache["evaluations"]:
            d = cache["evaluations"][job.url]
            result = EvaluationResult(job=job, **d)
            print(f"  Evaluating: {job.title} at {job.company} (cached, {result.tier})")
        else:
            print(f"  Evaluating: {job.title} at {job.company}")
            result = evaluate_job(job, config)
            cache["evaluations"][job.url] = _eval_to_dict(result)
            _save_cache(cache_file, cache)
        results.append(result)

    report_path = generate_report(
        results,
        reports_dir=reports_dir,
        searched_queries=len(queries),
        found_count=len(all_jobs),
    )
    strong = sum(1 for r in results if r.tier == "Strong Match")
    possible = sum(1 for r in results if r.tier == "Possible")
    skip = sum(1 for r in results if r.tier == "Skip")
    print(f"\nReport written to: {report_path}")
    print(f"Strong Match: {strong} | Possible: {possible} | Skip: {skip}")
    return report_path


if __name__ == "__main__":
    main()

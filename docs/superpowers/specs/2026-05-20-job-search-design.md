# Job Search Skill — Design Spec
**Date:** 2026-05-20

## Overview

A Claude Code skill (`/job-search`) that searches LinkedIn for Senior AI/ML Engineer positions matching the user's profile and criteria. It uses the Claude API with web search to find and evaluate listings, then writes a tiered markdown report.

---

## File Structure

```
eval_example/
  skills/
    job-search/
      SKILL.md              # Claude Code skill entrypoint
  config.yaml               # User-editable criteria and search config
  job_search.py             # Main script: search + evaluate + report
  prompts/
    evaluate_job.md         # Evaluation prompt template with scoring rubric
  reports/                  # Auto-created; one .md file per run
    job-search-YYYY-MM-DD.md
```

---

## Components

### SKILL.md
- Frontmatter: `name: job-search`, description triggers when user wants to find jobs
- Body: instructs Claude to run `python job_search.py` from the `eval_example/` directory
- No parameters — all configuration lives in `config.yaml`

### config.yaml
User-editable file defining the full search and evaluation criteria:

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

### job_search.py
Orchestrates the full pipeline:

1. Load `config.yaml`
2. For each search query, call Claude API with `web_search` tool to find LinkedIn job URLs
3. For each URL, call Claude API with `web_search` to extract job details (title, company, location, salary, description)
4. Call Claude API with `evaluate_job.md` prompt + job details + criteria → returns structured tier + reasoning
5. Collect results, sort by tier, write `reports/job-search-YYYY-MM-DD.md`

Uses `anthropic` Python SDK. Model: `claude-sonnet-4-6`.

### prompts/evaluate_job.md
Evaluation prompt template with explicit scoring rubric:

- Receives: job details (title, company, location, salary, description) + full criteria from config
- Returns structured JSON: `{ "tier": "Strong Match|Possible|Skip", "matched_required": [...], "matched_preferred": [...], "deal_breakers_hit": [...], "reasoning": "2 sentences" }`

**Tiering logic:**
- **Strong Match**: no deal-breakers + all required criteria met + 3 or more preferred criteria met
- **Possible**: no deal-breakers + all required criteria met + fewer than 3 preferred criteria met
- **Skip**: any deal-breaker hit, OR any required criterion not met

### reports/job-search-YYYY-MM-DD.md
One file per run. Format:

```markdown
# Job Search Report — YYYY-MM-DD

## Summary
- Searched: N queries | Found: N listings | Evaluated: N
- Strong Match: N | Possible: N | Skip: N

---

## Strong Match

### 1. {Role} — {Company}
- **URL**: {linkedin_url}
- **Location**: {location}
- **Salary**: {salary or "Not listed"}
- **Matched required**: {list}
- **Matched preferred**: {list}
- **Why**: {2-sentence reasoning}

---

## Possible
...

## Skip
...
```

---

## Data Flow

```
User invokes /job-search
       ↓
Claude runs: python job_search.py
       ↓
Script reads config.yaml
       ↓
For each search query:
  Claude API (web_search) → LinkedIn job URLs
       ↓
For each URL:
  Claude API (web_search) → job details
       ↓
  Claude API (evaluate_job.md prompt) → tier + reasoning
       ↓
Write reports/job-search-YYYY-MM-DD.md
```

---

## Dependencies

- `anthropic` Python SDK (Claude API)
- `pyyaml` for config parsing
- `pathlib`, `datetime` (stdlib)
- Claude model: `claude-sonnet-4-6`
- Web search tool: built-in via Claude API

---

## Out of Scope (v1)

- Other job platforms (Indeed, Glassdoor) — LinkedIn only
- Deduplication across runs
- Email/notification delivery
- Automatic CV tailoring per listing

---
name: job-search
description: Search LinkedIn for Senior AI/ML Engineer job listings matching your profile. Finds, evaluates, and ranks jobs into Strong Match / Possible / Skip. Run this when you want to find new job opportunities.
---

Run the job search pipeline:

```bash
python3 job_search.py
```

The script reads `config.yaml` for all search queries and evaluation criteria, then writes a ranked report to `reports/job-search-YYYY-MM-DD.md`.

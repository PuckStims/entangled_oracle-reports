# Phase 8 QA Workflow

Run the full local QA workflow with one command:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_phase8_qa.ps1
```

This workflow does two things in order:

1. Runs the Python unittest suite in `tests/`.
2. Generates the fixed manual review pack in `output/phase8_review_pack/`.

Artifacts written by the review-pack step:

- `output/phase8_review_pack/html/`
- `output/phase8_review_pack/review_pack_manifest.json`
- `output/phase8_review_pack/review_checklist.md`

The manual review pack always includes:

- `Year Ahead`
- `Personal Forecast`
- `Soul Ecosystem`
- `Horoscope`
- `Simple DOB-only Horoscope`

For PDF verification, treat the generated HTML as the source of truth and follow:

- `products/shared/REPORT_PDF_WORKFLOW.md`

# Test Suite (`tests/`)

This directory contains the automated test suite for the SPrav Job Application pipeline, built using the `pytest` framework. 

Given the high stakes of an automated job application system, tests here are heavily focused on ensuring strict adherence to logic gates, preventing hallucinations, and guaranteeing data integrity during the parsing process.

---

## 🧪 Test Coverage Areas

### Engine Logic (`test_engine.py`)
Validates the prompt generation, threshold evaluation, and state transitions of the core AI pipeline.
- Ensures the DeepSeek-R1 logic prompt is constructed correctly with the user's canonical `me.json` data.
- Validates the JSON schema outputs of the LLM parser.
- Asserts that the `Application Scope` gating logic correctly rejects out-of-scope locations and job types before invoking LLMs.

### Intake & Parsing (`test_intake.py`)
Tests the heavily complex "Phase 0" onboarding engine. This module parses unstructured resumes and LinkedIn data exports and normalizes them into the strict `me.json` schema.
- **Normalization Tests**: Ensures dates are correctly parsed and overlapping tenures are flagged.
- **Deduplication Tests**: Verifies that merging a LinkedIn export and an old PDF resume does not create duplicate roles for the same company.
- **Missing Data Tests**: Validates that if a resume bullet is missing a measurable metric, the system correctly flags it into the `needs_detail` queue for manual user input.

## 🚀 Running the Tests

To run the entire suite locally:
```bash
python -m pytest tests/ -v
```

To run a specific test file:
```bash
python -m pytest tests/test_intake.py -v
```

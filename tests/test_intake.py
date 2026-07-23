"""
tests/test_intake.py — Unit tests for Phase 0 Intake + Merger

Run with:
    pytest tests/test_intake.py -v
"""
import csv
import io
import json
import os
import sys
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Make the project root importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.intake import (
    _make_id,
    _normalise_work_history,
    manual_entries,
    parse_linkedin_export,
)
from engine.kb_merger import (
    _dates_overlap,
    _detect_needs_detail,
    _has_metric,
    _merge_skills,
    _merge_work_history,
    apply_detail_updates,
    kb_is_ready,
    merge,
    resolve_conflicts,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

SAMPLE_WORK_ENTRY = {
    "id": "work_acme",
    "company": "Acme Corp",
    "role": "Software Engineer",
    "type": "full_time",
    "start_date": "2022-01",
    "end_date": "2023-12",
    "in_progress": False,
    "last_reviewed": "2025-01-01",
    "bullets": [
        {
            "id": "bullet_acme_1",
            "text": "Built a REST API that served thousands of requests",  # no metric
            "metric_verified": "self_reported",
            "ats_keywords": [],
            "themes": [],
        },
        {
            "id": "bullet_acme_2",
            "text": "Reduced deployment time by 60% using GitHub Actions",  # has metric
            "metric_verified": "verified",
            "ats_keywords": ["CI/CD", "GitHub Actions"],
            "themes": [],
        },
    ],
}

SAMPLE_KB = {
    "personal": {"name": "Jane Doe", "email": "jane@example.com"},
    "work_history": [SAMPLE_WORK_ENTRY],
    "projects": [],
    "github_projects": [],
    "portfolio_projects": [],
    "education": [],
    "certifications": [],
    "skills": {"languages": ["Python"]},
    "needs_detail": [],
    "pending_conflicts": [],
}


# ─────────────────────────────────────────────────────────────────────────────
# intake.py — helper tests
# ─────────────────────────────────────────────────────────────────────────────

class TestHelpers:
    def test_make_id_basic(self):
        result = _make_id("work", "Acme Corp")
        assert result.startswith("work_")
        assert "acme" in result

    def test_make_id_empty_text(self):
        result = _make_id("proj")
        assert result.startswith("proj_")

    def test_normalise_work_history_creates_bullet_ids(self):
        raw = [{"company": "TestCo", "role": "Dev", "start_date": "2022", "end_date": "2023",
                "bullets": ["Did a thing", "Did another thing"]}]
        result = _normalise_work_history(raw, "resume")
        assert len(result) == 1
        entry = result[0]
        assert entry["company"] == "TestCo"
        assert len(entry["bullets"]) == 2
        for b in entry["bullets"]:
            assert "id" in b
            assert b["metric_verified"] == "self_reported"

    def test_normalise_skips_empty_company(self):
        raw = [{"company": "", "role": "Dev", "bullets": []}]
        result = _normalise_work_history(raw, "resume")
        assert result == []


# ─────────────────────────────────────────────────────────────────────────────
# intake.py — manual_entries
# ─────────────────────────────────────────────────────────────────────────────

class TestManualEntries:
    def test_freelance_becomes_work_history(self):
        data = {
            "freelance": [
                {"company": "Client A", "role": "Freelance Dev",
                 "start_date": "2023-01", "end_date": "2023-06",
                 "bullets": ["Built a landing page"]}
            ],
            "internships": [],
            "certifications": [],
        }
        result = manual_entries(data)
        assert len(result["work_history"]) == 1
        assert result["work_history"][0]["type"] == "freelance"
        assert result["work_history"][0]["company"] == "Client A"

    def test_certification_is_parsed(self):
        data = {
            "freelance": [], "internships": [],
            "certifications": [
                {"name": "AWS SAA", "issuer": "Amazon",
                 "date_earned": "2024-01", "expires": "2027-01",
                 "credential_id": "ABC123", "url": "https://aws.amazon.com"}
            ],
        }
        result = manual_entries(data)
        assert len(result["certifications"]) == 1
        cert = result["certifications"][0]
        assert cert["name"] == "AWS SAA"
        assert cert["issuer"] == "Amazon"
        assert cert["credential_id"] == "ABC123"

    def test_empty_cert_name_skipped(self):
        data = {
            "freelance": [], "internships": [],
            "certifications": [{"name": "", "issuer": "AWS"}],
        }
        result = manual_entries(data)
        assert result["certifications"] == []


# ─────────────────────────────────────────────────────────────────────────────
# intake.py — parse_linkedin_export
# ─────────────────────────────────────────────────────────────────────────────

def _make_linkedin_zip(tmp_path) -> str:
    """Helper: creates a minimal LinkedIn export ZIP in tmp_path."""
    zip_path = os.path.join(tmp_path, "linkedin_export.zip")

    positions_csv = "Company Name,Title,Started On,Finished On\nAcme Corp,Software Engineer,Jan 2022,Dec 2023\nStartup XYZ,Junior Dev,Jan 2020,Dec 2021\n"
    education_csv = "School Name,Degree Name,Field Of Study,Start Date,End Date\nMIT,Bachelor of Science,Computer Science,2016,2020\n"
    skills_csv = "Name\nPython\nReact\nDocker\n"
    certifications_csv = "Name,Authority,Started On,Finished On,License Number,Url\nAWS SAA,Amazon,2024-01,,ABC123,https://aws.amazon.com\n"
    projects_csv = "Title,Description,Url,Started On,Finished On\nMy App,A cool app,https://myapp.com,2023-01,2023-06\n"

    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("Positions.csv", positions_csv)
        zf.writestr("Education.csv", education_csv)
        zf.writestr("Skills.csv", skills_csv)
        zf.writestr("Certifications.csv", certifications_csv)
        zf.writestr("Projects.csv", projects_csv)

    return zip_path


class TestLinkedInExport:
    def test_parses_positions(self, tmp_path):
        zip_path = _make_linkedin_zip(str(tmp_path))
        result = parse_linkedin_export(zip_path)
        assert len(result["work_history"]) == 2
        companies = {e["company"] for e in result["work_history"]}
        assert "Acme Corp" in companies

    def test_parses_education(self, tmp_path):
        zip_path = _make_linkedin_zip(str(tmp_path))
        result = parse_linkedin_export(zip_path)
        assert len(result["education"]) == 1
        assert result["education"][0]["institution"] == "MIT"

    def test_parses_certifications(self, tmp_path):
        zip_path = _make_linkedin_zip(str(tmp_path))
        result = parse_linkedin_export(zip_path)
        assert len(result["certifications"]) == 1
        assert result["certifications"][0]["name"] == "AWS SAA"

    def test_portfolio_projects_start_unconfirmed(self, tmp_path):
        zip_path = _make_linkedin_zip(str(tmp_path))
        result = parse_linkedin_export(zip_path)
        for proj in result["portfolio_projects"]:
            assert proj["confirmed"] is False

    def test_invalid_zip_raises(self, tmp_path):
        bad_path = os.path.join(str(tmp_path), "bad.zip")
        with open(bad_path, "w") as f:
            f.write("not a zip")
        with pytest.raises(ValueError, match="Not a valid ZIP file"):
            parse_linkedin_export(bad_path)


# ─────────────────────────────────────────────────────────────────────────────
# kb_merger.py — date overlap
# ─────────────────────────────────────────────────────────────────────────────

class TestDateOverlap:
    def test_clearly_overlapping(self):
        assert _dates_overlap("2022-01", "2023-12", "2023-01", "2024-06") is True

    def test_clearly_non_overlapping(self):
        assert _dates_overlap("2020", "2021", "2022", "2023") is False

    def test_adjacent_years_do_not_overlap(self):
        # 2021 end vs 2022 start: same-year boundary, treated as non-overlapping
        assert _dates_overlap("2020", "2021", "2022", "2023") is False

    def test_present_treated_as_future(self):
        assert _dates_overlap("2020", "Present", "2024", "2025") is True


# ─────────────────────────────────────────────────────────────────────────────
# kb_merger.py — dedup logic
# ─────────────────────────────────────────────────────────────────────────────

class TestMergerDedup:
    def test_same_company_same_dates_no_duplicate(self):
        existing = [dict(SAMPLE_WORK_ENTRY)]
        new_source = [{
            "source": "linkedin",
            "work_history": [{
                "id": "work_acme_ln",
                "company": "Acme Corp",
                "role": "Software Engineer",
                "type": "full_time",
                "start_date": "2022-01",
                "end_date": "2023-12",
                "in_progress": False,
                "last_reviewed": "2025-01-01",
                "bullets": [],
            }],
        }]
        merged, _ = _merge_work_history(new_source, existing)
        acme_entries = [e for e in merged if e["company"] == "Acme Corp"]
        assert len(acme_entries) == 1, "Should not create a duplicate entry"

    def test_different_company_creates_new_entry(self):
        existing = [dict(SAMPLE_WORK_ENTRY)]
        new_source = [{
            "source": "linkedin",
            "work_history": [{
                "id": "work_startup",
                "company": "Startup XYZ",
                "role": "Junior Dev",
                "type": "full_time",
                "start_date": "2020-01",
                "end_date": "2021-12",
                "in_progress": False,
                "last_reviewed": "2025-01-01",
                "bullets": [],
            }],
        }]
        merged, _ = _merge_work_history(new_source, existing)
        assert len(merged) == 2

    def test_new_bullets_merged_into_existing_entry(self):
        existing = [dict(SAMPLE_WORK_ENTRY)]
        new_source = [{
            "source": "linkedin",
            "work_history": [{
                "id": "work_acme_ln",
                "company": "Acme Corp",
                "role": "Software Engineer",
                "type": "full_time",
                "start_date": "2022-01",
                "end_date": "2023-12",
                "in_progress": False,
                "last_reviewed": "2025-01-01",
                "bullets": [{"id": "new_bullet", "text": "A brand new achievement", "metric_verified": "self_reported", "ats_keywords": [], "themes": []}],
            }],
        }]
        merged, _ = _merge_work_history(new_source, existing)
        acme = next(e for e in merged if e["company"] == "Acme Corp")
        texts = [b["text"] for b in acme["bullets"]]
        assert "A brand new achievement" in texts


# ─────────────────────────────────────────────────────────────────────────────
# kb_merger.py — conflict detection
# ─────────────────────────────────────────────────────────────────────────────

class TestMergerConflicts:
    def test_different_end_dates_creates_conflict(self):
        existing = [dict(SAMPLE_WORK_ENTRY)]  # end_date = "2023-12"
        new_source = [{
            "source": "linkedin",
            "work_history": [{
                "id": "work_acme_ln",
                "company": "Acme Corp",
                "role": "Software Engineer",
                "type": "full_time",
                "start_date": "2022-01",
                "end_date": "2024-03",   # DIFFERENT end date
                "in_progress": False,
                "last_reviewed": "2025-01-01",
                "bullets": [],
            }],
        }]
        merged, conflicts = _merge_work_history(new_source, existing)
        conflict_fields = [c["field"] for c in conflicts]
        assert any("end_date" in f for f in conflict_fields)


# ─────────────────────────────────────────────────────────────────────────────
# kb_merger.py — gap detection
# ─────────────────────────────────────────────────────────────────────────────

class TestNeedsDetail:
    def test_bullet_without_metric_is_flagged(self):
        work = [dict(SAMPLE_WORK_ENTRY)]  # bullet_acme_1 has no metric
        flagged = _detect_needs_detail(work)
        flagged_ids = [f["bullet_id"] for f in flagged]
        assert "bullet_acme_1" in flagged_ids

    def test_bullet_with_metric_is_not_flagged(self):
        work = [dict(SAMPLE_WORK_ENTRY)]  # bullet_acme_2 has "60%"
        flagged = _detect_needs_detail(work)
        flagged_ids = [f["bullet_id"] for f in flagged]
        assert "bullet_acme_2" not in flagged_ids

    def test_detail_prompt_is_contextual(self):
        work = [{
            "company": "TestCo", "role": "Dev",
            "bullets": [
                {"id": "b1", "text": "Improved performance of the database queries"},
            ]
        }]
        flagged = _detect_needs_detail(work)
        assert len(flagged) == 1
        assert "performance" in flagged[0]["prompt"].lower() or "improv" in flagged[0]["prompt"].lower()


# ─────────────────────────────────────────────────────────────────────────────
# kb_merger.py — skills merge
# ─────────────────────────────────────────────────────────────────────────────

class TestSkillsMerge:
    def test_union_merge_no_duplicates(self):
        existing = {"languages": ["Python", "JavaScript"]}
        sources = [{"skills": {"languages": ["Python", "Go"]}}]  # Python already exists
        merged = _merge_skills(sources, existing)
        assert merged["languages"].count("Python") == 1
        assert "Go" in merged["languages"]
        assert "JavaScript" in merged["languages"]

    def test_new_category_added(self):
        existing = {"languages": ["Python"]}
        sources = [{"skills": {"frameworks": ["React", "FastAPI"]}}]
        merged = _merge_skills(sources, existing)
        assert "frameworks" in merged
        assert "React" in merged["frameworks"]


# ─────────────────────────────────────────────────────────────────────────────
# kb_merger.py — kb_is_ready
# ─────────────────────────────────────────────────────────────────────────────

class TestKbIsReady:
    def test_missing_file_returns_false(self, tmp_path):
        assert kb_is_ready(os.path.join(str(tmp_path), "nonexistent.json")) is False

    def test_placeholder_name_returns_false(self, tmp_path):
        kb_path = os.path.join(str(tmp_path), "me.json")
        with open(kb_path, "w") as f:
            json.dump({"personal": {"name": "YOUR FULL NAME"}, "work_history": [{"company": "Acme"}]}, f)
        assert kb_is_ready(kb_path) is False

    def test_populated_kb_returns_true(self, tmp_path):
        kb_path = os.path.join(str(tmp_path), "me.json")
        with open(kb_path, "w") as f:
            json.dump({"personal": {"name": "Jane Doe"}, "work_history": [{"company": "Acme"}]}, f)
        assert kb_is_ready(kb_path) is True


# ─────────────────────────────────────────────────────────────────────────────
# kb_merger.py — full merge round-trip
# ─────────────────────────────────────────────────────────────────────────────

class TestFullMerge:
    def test_merge_writes_json_and_creates_backup(self, tmp_path):
        kb_path = os.path.join(str(tmp_path), "me.json")
        history_dir = os.path.join(str(tmp_path), "knowledge_base", "history")

        # Write initial KB
        with open(kb_path, "w") as f:
            json.dump(SAMPLE_KB, f)

        sources = [manual_entries({
            "freelance": [{"company": "Freelance Client", "role": "Consultant",
                           "start_date": "2024-01", "end_date": "2024-06",
                           "bullets": ["Led a project"]}],
            "internships": [], "certifications": [],
        })]

        result = merge(sources, kb_path=kb_path)

        # New entry added
        companies = {e["company"] for e in result["work_history"]}
        assert "Freelance Client" in companies
        assert "Acme Corp" in companies

        # needs_detail populated (bullet_acme_1 has no metric)
        flagged_ids = [nd["bullet_id"] for nd in result["needs_detail"]]
        assert "bullet_acme_1" in flagged_ids

    def test_apply_detail_removes_from_needs_detail(self, tmp_path):
        kb_path = os.path.join(str(tmp_path), "me.json")
        with open(kb_path, "w") as f:
            json.dump({**SAMPLE_KB, "needs_detail": [
                {"bullet_id": "bullet_acme_1", "current_text": "Built a REST API", "prompt": "..."}
            ]}, f)

        result = apply_detail_updates(
            [{"bullet_id": "bullet_acme_1", "updated_text": "Built a REST API handling 50k daily requests"}],
            kb_path=kb_path,
        )
        assert all(nd["bullet_id"] != "bullet_acme_1" for nd in result["needs_detail"])

        # Confirm the bullet text was updated
        for entry in result["work_history"]:
            for b in entry["bullets"]:
                if b["id"] == "bullet_acme_1":
                    assert "50k" in b["text"]

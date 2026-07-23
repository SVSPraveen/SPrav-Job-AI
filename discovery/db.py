import sqlite3
import os
import hashlib
from datetime import date

DB_PATH = "jobs.db"


# ─────────────────────────────────────────────────────────────────────────────
# Schema initialisation
# ─────────────────────────────────────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ── Core jobs table ──────────────────────────────────────────────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            title TEXT,
            company TEXT,
            url TEXT,
            description TEXT,
            location TEXT,
            source TEXT,
            fit_score REAL DEFAULT 0.0,
            scam_flags TEXT,
            status TEXT DEFAULT 'new',
            updated_at TEXT,
            jd_hash TEXT,
            missing_skills TEXT,
            matched_skills TEXT,
            strategy_report TEXT,
            evaluation_rubric TEXT,
            contact_message TEXT,
            star_stories TEXT,
            ats_score REAL DEFAULT 0.0,
            disagreement_reason TEXT
        )
    ''')

    # ── Auto-apply audit log ─────────────────────────────────────────────────
    # Records every Playwright submission attempt for audit and circuit-breaker
    # tracking. Never deleted — provides a full tamper-evident application log.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS auto_apply_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            company TEXT,
            title TEXT,
            jd_hash TEXT,
            resume_version TEXT,           -- SHA-256 hex of the PDF file path
            attempted_at TEXT NOT NULL,    -- ISO-8601 UTC timestamp
            ats_score REAL DEFAULT 0.0,
            fit_score REAL DEFAULT 0.0,
            status TEXT NOT NULL           -- 'submitted'|'failed'|'deduped'|'capped'|'circuit_open'|'downgraded'
        )
    ''')

    # ── Daemon persistent state ───────────────────────────────────────────────
    # Key-value store for daemon state that must survive restarts (circuit
    # breaker counter, pause flag). Using a table is simpler than a sidecar file.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daemon_state (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')

    # Migrate: add disagreement_reason if upgrading from an older jobs.db
    try:
        cursor.execute("ALTER TABLE jobs ADD COLUMN disagreement_reason TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists

    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Core job helpers (unchanged)
# ─────────────────────────────────────────────────────────────────────────────

def save_job(job: dict):
    """Saves or updates a job in the database using named parameters for safety."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO jobs (id, title, company, url, description, location, source, fit_score, scam_flags, status)
        VALUES (:id, :title, :company, :url, :description, :location, :source, :fit_score, :scam_flags, :status)
        ON CONFLICT(id) DO UPDATE SET
            title=excluded.title,
            company=excluded.company,
            url=excluded.url,
            description=excluded.description,
            location=excluded.location,
            source=excluded.source,
            fit_score=excluded.fit_score,
            scam_flags=excluded.scam_flags
    ''', job)
    conn.commit()
    conn.close()


def get_jobs(status: str = None) -> list[dict]:
    """Fetches jobs from the DB using sqlite3.Row for column-safe dict conversion."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if status:
        cursor.execute("SELECT * FROM jobs WHERE status = ?", (status,))
    else:
        cursor.execute("SELECT * FROM jobs")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ─────────────────────────────────────────────────────────────────────────────
# Auto-apply safety helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_company_applies_today(company: str) -> int:
    """
    Returns the count of successful auto-apply submissions to `company` today.
    Used to enforce the per-company daily cap (COMPANY_DAILY_CAP in config.py).
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    today = date.today().isoformat()
    cursor.execute(
        """SELECT COUNT(*) FROM auto_apply_audit
           WHERE company = ?
             AND status = 'submitted'
             AND substr(attempted_at, 1, 10) = ?""",
        (company, today)
    )
    count = cursor.fetchone()[0]
    conn.close()
    return count


def has_been_applied_to(jd_hash: str, company: str, title: str) -> bool:
    """
    Returns True if we have a successful 'submitted' record for this exact job
    (matched by jd_hash OR the company+title combo) to prevent double-applying.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """SELECT 1 FROM auto_apply_audit
           WHERE status = 'submitted'
             AND (jd_hash = ? OR (company = ? AND title = ?))
           LIMIT 1""",
        (jd_hash, company, title)
    )
    result = cursor.fetchone() is not None
    conn.close()
    return result


def resume_version(pdf_path: str) -> str:
    """Returns a short SHA-256 hex of the PDF file path as a resume version tag."""
    return hashlib.sha256(pdf_path.encode()).hexdigest()[:16]


def log_auto_apply_attempt(
    job_id: str,
    company: str,
    title: str,
    jd_hash: str,
    pdf_path: str,
    ats_score: float,
    fit_score: float,
    status: str,
) -> None:
    """
    Appends a row to the auto_apply_audit table.
    `status` should be one of: 'submitted', 'failed', 'deduped', 'capped',
    'circuit_open', 'downgraded'.
    """
    from datetime import datetime, timezone
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO auto_apply_audit
               (job_id, company, title, jd_hash, resume_version,
                attempted_at, ats_score, fit_score, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            job_id, company, title, jd_hash,
            resume_version(pdf_path),
            datetime.now(timezone.utc).isoformat(),
            ats_score, fit_score, status,
        )
    )
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Daemon persistent state (circuit breaker)
# ─────────────────────────────────────────────────────────────────────────────

def get_daemon_state(key: str, default: str = "") -> str:
    """Reads a daemon state value from the daemon_state table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM daemon_state WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default


def set_daemon_state(key: str, value: str) -> None:
    """Upserts a daemon state value."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO daemon_state (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value)
    )
    conn.commit()
    conn.close()

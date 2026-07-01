import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "provenance.db")


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            content_id       TEXT PRIMARY KEY,
            creator_id       TEXT NOT NULL,
            timestamp        TEXT NOT NULL,
            attribution      TEXT NOT NULL,
            confidence       REAL NOT NULL,
            groq_score       REAL NOT NULL,
            stylometric_score REAL NOT NULL,
            status           TEXT NOT NULL DEFAULT 'classified',
            appeal_reasoning TEXT
        )
    """)
    conn.commit()
    conn.close()


def log_submission(
    content_id,
    creator_id,
    timestamp,
    attribution,
    confidence,
    groq_score,
    stylometric_score,
    status="classified",
    appeal_reasoning=None,
):
    conn = _get_conn()
    conn.execute(
        """
        INSERT INTO audit_log
            (content_id, creator_id, timestamp, attribution, confidence,
             groq_score, stylometric_score, status, appeal_reasoning)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            content_id,
            creator_id,
            timestamp,
            attribution,
            confidence,
            groq_score,
            stylometric_score,
            status,
            appeal_reasoning,
        ),
    )
    conn.commit()
    conn.close()


def update_appeal(content_id, reasoning) -> bool:
    conn = _get_conn()
    cursor = conn.execute(
        """
        UPDATE audit_log
        SET status = 'under_review', appeal_reasoning = ?
        WHERE content_id = ?
        """,
        (reasoning, content_id),
    )
    conn.commit()
    changed = cursor.rowcount > 0
    conn.close()
    return changed


def get_log(limit=50) -> list:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_entry(content_id) -> dict | None:
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM audit_log WHERE content_id = ?",
        (content_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None

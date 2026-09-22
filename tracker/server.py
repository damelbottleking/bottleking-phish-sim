#!/usr/bin/env python3
"""
Sidecar tracker for GoPhish campaigns.

GoPhish natively tracks clicks and form submissions.
This service records partial engagement (page view, field focus, field filled)
so you can export three lists:
  1. Clicked the link
  2. Clicked and interacted with the form but did not submit
  3. Clicked, filled, and submitted
"""

import csv
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, make_response, request

APP = Flask(__name__)


@APP.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response
DB_PATH = Path(__file__).resolve().parent / "tracker.db"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rid TEXT NOT NULL,
                stage TEXT NOT NULL,
                field TEXT,
                ip TEXT,
                user_agent TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_events_rid ON events(rid)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_events_stage ON events(stage)"
        )


@APP.route("/health")
def health():
    return jsonify({"status": "ok"})


@APP.route("/track", methods=["GET", "POST", "OPTIONS"])
def track():
    if request.method == "OPTIONS":
        return make_response("", 204)
    rid = (request.args.get("rid") or "").strip()
    stage = (request.args.get("stage") or "").strip()
    field = (request.args.get("field") or "").strip() or None

    if not rid or not stage:
        return ("missing rid or stage", 400)

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO events (rid, stage, field, ip, user_agent, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                rid,
                stage,
                field,
                request.remote_addr,
                request.headers.get("User-Agent", ""),
                utc_now(),
            ),
        )

    return ("", 204)


@APP.route("/stats")
def stats():
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT stage, COUNT(*) AS count
            FROM events
            GROUP BY stage
            ORDER BY count DESC
            """
        ).fetchall()

    return jsonify({row["stage"]: row["count"] for row in rows})


@APP.route("/export/<rid>")
def export_rid(rid: str):
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT stage, field, created_at
            FROM events
            WHERE rid = ?
            ORDER BY created_at ASC
            """,
            (rid,),
        ).fetchall()

    return jsonify([dict(row) for row in rows])


def main() -> None:
    init_db()
    host = os.environ.get("TRACKER_HOST", "127.0.0.1")
    port = int(os.environ.get("TRACKER_PORT", "9090"))
    APP.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()

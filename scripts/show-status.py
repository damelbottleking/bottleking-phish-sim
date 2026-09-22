#!/usr/bin/env python3
"""Print GoPhish campaign counts and tracker partial-fill stats."""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOPHISH_DB = ROOT / "gophish-bin" / "gophish.db"
TRACKER_DB = ROOT / "tracker" / "tracker.db"


def main() -> None:
    print("=== GoPhish results ===")
    conn = sqlite3.connect(GOPHISH_DB)
    rows = conn.execute(
        """
        SELECT r.email, r.status, r.r_id, r.modified_date
        FROM results r
        ORDER BY r.modified_date DESC
        """
    ).fetchall()
    counts: dict[str, int] = {}
    for email, status, rid, modified in rows:
        counts[status] = counts.get(status, 0) + 1
        print(f"  {email:30} {status:20} rid={rid}  ({modified})")
    print("\nBreakdown:")
    for status, count in sorted(counts.items()):
        print(f"  {status}: {count}")
    conn.close()

    if TRACKER_DB.exists():
        print("\n=== Tracker partial engagement ===")
        conn = sqlite3.connect(TRACKER_DB)
        rows = conn.execute(
            "SELECT rid, stage, COUNT(*) FROM events GROUP BY rid, stage ORDER BY rid, stage"
        ).fetchall()
        if not rows:
            print("  (no events — GitHub form was not wired to tracker yet, or tunnels not running)")
        for rid, stage, count in rows:
            print(f"  {rid}  {stage}: {count}")
        conn.close()


if __name__ == "__main__":
    main()

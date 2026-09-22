#!/usr/bin/env python3
"""
Export three CSV lists from a GoPhish campaign + tracker sidecar:

1. clicked.csv        - opened email link
2. partial_fill.csv   - clicked and interacted with form, did not submit
3. submitted.csv      - clicked, filled form, and submitted
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sqlite3
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TRACKER_DB = ROOT / "tracker" / "tracker.db"
OUTPUT_DIR = ROOT / "data" / "exports"

INTERACTION_STAGES = {
    "page_view",
    "field_focus",
    "field_filled",
    "form_submit_attempt",
}
PARTIAL_FILL_STAGES = {"field_focus", "field_filled"}


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def api_get(base_url: str, api_key: str, path: str) -> Any:
    url = base_url.rstrip("/") + path
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {api_key}"},
        method="GET",
    )
    ctx = urllib.request.ssl._create_unverified_context()
    with urllib.request.urlopen(req, context=ctx) as resp:
        return json.loads(resp.read().decode("utf-8"))


def find_campaign_id(base_url: str, api_key: str, campaign_name: str) -> int:
    campaigns = api_get(base_url, api_key, "/api/campaigns/")
    for campaign in campaigns:
        if campaign.get("name") == campaign_name:
            return int(campaign["id"])
    names = ", ".join(c.get("name", "?") for c in campaigns)
    raise SystemExit(f"Campaign not found: {campaign_name}. Existing: {names}")


def load_tracker_interactions(db_path: Path) -> dict[str, set[str]]:
    if not db_path.exists():
        return {}

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT rid, stage FROM events WHERE stage IN ({})".format(
            ",".join("?" for _ in INTERACTION_STAGES)
        ),
        tuple(INTERACTION_STAGES),
    ).fetchall()
    conn.close()

    interactions: dict[str, set[str]] = {}
    for row in rows:
        interactions.setdefault(row["rid"], set()).add(row["stage"])
    return interactions


def normalize_status(status: str) -> str:
    return (status or "").strip().lower()


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["first_name", "last_name", "email", "position", "status", "rid"]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> None:
    parser = argparse.ArgumentParser(description="Export GoPhish campaign results")
    parser.add_argument("--campaign", help="Campaign name override")
    args = parser.parse_args()

    env = load_env(ROOT / ".env")
    base_url = env.get("GOPHISH_API_URL", "https://127.0.0.1:3333")
    api_key = env.get("GOPHISH_API_KEY", "")
    campaign_name = args.campaign or env.get("CAMPAIGN_NAME", "")

    if not api_key:
        raise SystemExit("Set GOPHISH_API_KEY in .env (GoPhish -> Settings -> API Key)")
    if not campaign_name:
        raise SystemExit("Set CAMPAIGN_NAME in .env or pass --campaign")

    campaign_id = find_campaign_id(base_url, api_key, campaign_name)
    results = api_get(base_url, api_key, f"/api/campaigns/{campaign_id}/results")
    interactions = load_tracker_interactions(TRACKER_DB)

    clicked: list[dict[str, str]] = []
    partial_fill: list[dict[str, str]] = []
    submitted: list[dict[str, str]] = []

    for result in results:
        row = {
            "first_name": result.get("first_name", ""),
            "last_name": result.get("last_name", ""),
            "email": result.get("email", ""),
            "position": result.get("position", ""),
            "status": result.get("status", ""),
            "rid": result.get("id", "") or result.get("rid", ""),
        }
        rid = str(result.get("id") or result.get("rid") or "")
        status = normalize_status(result.get("status", ""))

        clicked_statuses = {"clicked link", "submitted data"}
        if status in clicked_statuses:
            clicked.append(row)

        if status == "submitted data":
            submitted.append(row)
        elif status == "clicked link":
            stages = interactions.get(rid, set())
            if stages.intersection(PARTIAL_FILL_STAGES):
                partial_fill.append(row)

    write_csv(OUTPUT_DIR / "1-clicked.csv", clicked)
    write_csv(OUTPUT_DIR / "2-partial-fill.csv", partial_fill)
    write_csv(OUTPUT_DIR / "3-submitted.csv", submitted)

    print(f"Exported to {OUTPUT_DIR}")
    print(f"  1-clicked.csv:       {len(clicked)}")
    print(f"  2-partial-fill.csv:  {len(partial_fill)}")
    print(f"  3-submitted.csv:     {len(submitted)}")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.URLError as exc:
        raise SystemExit(f"Could not reach GoPhish API: {exc}") from exc

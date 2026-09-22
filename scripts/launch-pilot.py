#!/usr/bin/env python3
"""Launch the Daniel-only pilot campaign in GoPhish."""

from __future__ import annotations

import json
import sqlite3
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_env() -> dict[str, str]:
    values: dict[str, str] = {}
    for line in (ROOT / ".env").read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def api(method: str, base: str, key: str, path: str, body: dict | None = None):
    url = base.rstrip("/") + path
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method=method,
    )
    ctx = urllib.request.ssl._create_unverified_context()
    with urllib.request.urlopen(req, context=ctx) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def smtp_password_configured(base: str, key: str, profile_name: str) -> bool:
    db_path = ROOT / "gophish-bin" / "gophish.db"
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT password FROM smtp WHERE name = ? LIMIT 1",
        (profile_name,),
    ).fetchone()
    conn.close()
    if row and row[0]:
        return True

    profiles = api("GET", base, key, "/api/smtp/")
    smtp = next((s for s in profiles if s.get("name") == profile_name), None)
    return bool(smtp and smtp.get("password"))


def read_admin_api_key() -> str:
    db_path = ROOT / "gophish-bin" / "gophish.db"
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT api_key FROM users WHERE username = 'admin' LIMIT 1"
    ).fetchone()
    conn.close()
    if not row or not row[0]:
        raise SystemExit("Admin API key not found.")
    return row[0]


def main() -> None:
    force = "--force" in sys.argv
    env = load_env()
    base = env["GOPHISH_API_URL"]
    key = env.get("GOPHISH_API_KEY") or read_admin_api_key()
    campaign_name = env["CAMPAIGN_NAME"]
    pilot_email = "daniel.e@bottleking.ng"

    campaigns = api("GET", base, key, "/api/campaigns/")
    campaign = next((c for c in campaigns if c.get("name") == campaign_name), None)

    if not smtp_password_configured(base, key, env["SMTP_PROFILE_NAME"]):
        raise SystemExit(
            "SMTP password is empty. In GoPhish UI go to Sending Profiles -> "
            "BottleKing Kingsley SMTP -> add Google App Password -> Save, then rerun."
        )

    groups = api("GET", base, key, "/api/groups/")
    pilot_group = next((g for g in groups if g.get("name") == env["USER_GROUP_PILOT"]), None)
    if not pilot_group:
        raise SystemExit("Pilot group not found.")

    targets = pilot_group.get("targets", [])
    if not targets:
        raise SystemExit(f"Pilot group {env['USER_GROUP_PILOT']} has no targets.")

    send_name = campaign_name
    if campaign:
        results = api("GET", base, key, f"/api/campaigns/{campaign['id']}/results")
        if isinstance(results, dict):
            results = results.get("results", [])
        failed = any(r.get("status") == "Error" for r in results)
        sent = any(r.get("status") in {"Email Sent", "Clicked Link", "Submitted Data"} for r in results)
        if sent and not force:
            print(f"Campaign already sent successfully to {pilot_email}")
            print(f"Campaign id: {campaign['id']} status: {campaign.get('status')}")
            print("Run with --force to send a new tracked campaign (e.g. after tunnel URL change).")
            return
        if failed or campaign.get("status") in {"In progress", "Completed"}:
            send_name = f"{campaign_name} - Retry {datetime.now().strftime('%H%M')}"

    body = {
        "name": send_name,
        "template": {"name": env["EMAIL_TEMPLATE_NAME"]},
        "page": {"name": env["LANDING_PAGE_NAME"]},
        "smtp": {"name": env["SMTP_PROFILE_NAME"]},
        "url": env.get("GOPHISH_PUBLIC_URL") or env["PHISH_PUBLIC_URL"],
        "groups": [{"name": env["USER_GROUP_PILOT"]}],
        "launch_date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
    }
    created = api("POST", base, key, "/api/campaigns/", body)
    campaign_id = created["id"]
    status = created.get("status", "Created")

    print("Pilot campaign ready:")
    print(f"  Campaign: {campaign_name} (id {campaign_id})")
    print(f"  Status:   {status}")
    print(f"  To:       {pilot_email}")
    print(f"  From:     {env['SMTP_FROM_NAME']} <{env['SMTP_FROM_EMAIL']}>")
    print(f"  Campaign URL: {env.get('GOPHISH_PUBLIC_URL') or env['PHISH_PUBLIC_URL']}")
    print(f"  Form URL:     {env['PHISH_PUBLIC_URL']}")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"GoPhish API error {exc.code}: {detail}") from exc

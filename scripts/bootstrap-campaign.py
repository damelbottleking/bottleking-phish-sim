#!/usr/bin/env python3
"""Import GoPhish assets and create the pilot campaign via API."""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_env() -> dict[str, str]:
    values: dict[str, str] = {}
    env_path = ROOT / ".env"
    for line in env_path.read_text().splitlines():
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


def wait_for_api(base: str, key: str, timeout: int = 60) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            api("GET", base, key, "/api/campaigns/")
            return
        except Exception:
            time.sleep(2)
    raise SystemExit("GoPhish API not reachable. Is the server running?")


def read_admin_api_key() -> str:
    db_path = ROOT / "gophish-bin" / "gophish.db"
    if not db_path.exists():
        raise SystemExit("gophish.db not found. Start GoPhish first.")
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT api_key FROM users WHERE username = 'admin' LIMIT 1"
    ).fetchone()
    conn.close()
    if not row or not row[0]:
        raise SystemExit("Admin API key not found in database.")
    return row[0]


def load_csv_targets(path: Path) -> list[dict[str, str]]:
    import csv

    rows: list[dict[str, str]] = []
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append(
                {
                    "first_name": row["First Name"].strip(),
                    "last_name": row["Last Name"].strip(),
                    "email": row["Email"].strip(),
                    "position": row.get("Position", "").strip(),
                }
            )
    return rows


def upsert_group(base: str, key: str, name: str, csv_path: Path) -> int:
    targets = load_csv_targets(csv_path)
    existing = api("GET", base, key, "/api/groups/")
    for group in existing:
        if group.get("name") == name:
            body = {
                "id": group["id"],
                "name": name,
                "targets": targets,
            }
            updated = api("PUT", base, key, f"/api/groups/{group['id']}", body)
            return int(updated["id"])

    created = api(
        "POST",
        base,
        key,
        "/api/groups/",
        {"name": name, "targets": targets},
    )
    return int(created["id"])


def upsert_template(base: str, key: str, name: str, html_path: Path) -> int:
    html = html_path.read_text(encoding="utf-8")
    existing = api("GET", base, key, "/api/templates/")
    body = {
        "name": name,
        "subject": "STAFF WELFARE & INVESTMENT BENEFIT (Dangote Refinery Shares)",
        "html": html,
        "text": "",
    }
    for template in existing:
        if template.get("name") == name:
            body["id"] = template["id"]
            updated = api("PUT", base, key, f"/api/templates/{template['id']}", body)
            return int(updated["id"])

    created = api("POST", base, key, "/api/templates/", body)
    return int(created["id"])


def upsert_page(
    base: str,
    key: str,
    name: str,
    html_path: Path,
    *,
    capture_credentials: bool = True,
    redirect_url: str = "https://www.bottleking.ng",
) -> int:
    html = html_path.read_text(encoding="utf-8")
    existing = api("GET", base, key, "/api/pages/")
    body = {
        "name": name,
        "html": html,
        "capture_credentials": capture_credentials,
        "capture_passwords": False,
        "redirect_url": redirect_url,
    }
    for page in existing:
        if page.get("name") == name:
            body["id"] = page["id"]
            updated = api("PUT", base, key, f"/api/pages/{page['id']}", body)
            return int(updated["id"])

    created = api("POST", base, key, "/api/pages/", body)
    return int(created["id"])


def upsert_smtp(base: str, key: str, env: dict[str, str]) -> int:
    name = env["SMTP_PROFILE_NAME"]
    host = env["SMTP_HOST"]
    port = env.get("SMTP_PORT", "587")
    username = env["SMTP_USERNAME"]
    password = env.get("SMTP_PASSWORD", "")
    from_address = f"{env['SMTP_FROM_NAME']} <{env['SMTP_FROM_EMAIL']}>"

    existing = api("GET", base, key, "/api/smtp/")
    body = {
        "name": name,
        "interface_type": "SMTP",
        "from_address": from_address,
        "host": f"{host}:{port}",
        "username": username,
        "password": password,
        "ignore_cert_errors": False,
        "headers": [],
    }
    for profile in existing:
        if profile.get("name") == name:
            body["id"] = profile["id"]
            if not password:
                body["password"] = profile.get("password", "")
            updated = api("PUT", base, key, f"/api/smtp/{profile['id']}", body)
            return int(updated["id"])

    created = api("POST", base, key, "/api/smtp/", body)
    return int(created["id"])


def create_pilot_campaign(
    base: str,
    key: str,
    env: dict[str, str],
    group_id: int,
    template_id: int,
    page_id: int,
    smtp_id: int,
) -> int:
    name = env["CAMPAIGN_NAME"]
    existing = api("GET", base, key, "/api/campaigns/")
    for campaign in existing:
        if campaign.get("name") == name:
            return int(campaign["id"])

    body = {
        "name": name,
        "template": {"name": env["EMAIL_TEMPLATE_NAME"]},
        "page": {"name": env["LANDING_PAGE_NAME"]},
        "smtp": {"name": env["SMTP_PROFILE_NAME"]},
        "url": env.get("GOPHISH_PUBLIC_URL") or env["PHISH_PUBLIC_URL"],
        "groups": [{"name": env["USER_GROUP_PILOT"]}],
    }
    created = api("POST", base, key, "/api/campaigns/", body)
    return int(created["id"])


def main() -> None:
    env = load_env()
    base = env.get("GOPHISH_API_URL", "https://127.0.0.1:3333")
    api_key = env.get("GOPHISH_API_KEY") or read_admin_api_key()

    wait_for_api(base, api_key)

    # Prepare landing page with tracker URL substitution
    tracker_base = env.get("TRACKER_PUBLIC_URL", env["PHISH_PUBLIC_URL"])
    landing_src = ROOT / "templates" / "landing-page.html"
    landing_ready = ROOT / "templates" / "prepared" / "landing-page-ready.html"
    landing_ready.parent.mkdir(parents=True, exist_ok=True)
    landing_ready.write_text(
        landing_src.read_text(encoding="utf-8").replace("__TRACKER_BASE__", tracker_base),
        encoding="utf-8",
    )

    group_id = upsert_group(
        base,
        api_key,
        env["USER_GROUP_PILOT"],
        ROOT / "data" / "staff-pilot-test.csv",
    )
    upsert_group(
        base,
        api_key,
        env["USER_GROUP_ALL"],
        ROOT / "data" / "staff-all.csv",
    )
    template_id = upsert_template(
        base,
        api_key,
        env["EMAIL_TEMPLATE_NAME"],
        ROOT / "templates" / "email-bottleking-update.html",
    )
    redirect_page = ROOT / "templates" / "gophish-redirect.html"
    page_id = upsert_page(
        base,
        api_key,
        env["LANDING_PAGE_NAME"],
        redirect_page,
        capture_credentials=False,
        redirect_url=env["PHISH_PUBLIC_URL"],
    )
    smtp_id = upsert_smtp(base, api_key, env)
    campaign_id = create_pilot_campaign(
        base,
        api_key,
        env,
        group_id,
        template_id,
        page_id,
        smtp_id,
    )

    print("GoPhish assets imported:")
    print(f"  Pilot group id:   {group_id} (daniel.e@bottleking.ng)")
    print(f"  All staff group:  imported ({env['USER_GROUP_ALL']})")
    print(f"  Template id:      {template_id}")
    print(f"  Landing page id:  {page_id}")
    print(f"  SMTP profile id:  {smtp_id}")
    print(f"  Pilot campaign:   {campaign_id} ({env['CAMPAIGN_NAME']})")
    print()
    print("Next:")
    print("  1. Open https://127.0.0.1:3333")
    print("  2. Sending Profiles -> BottleKing Kingsley SMTP -> add Google App Password")
    print("  3. Campaigns -> open pilot campaign -> Launch (or Send Test Email first)")
    print(f"     Campaign URL: {env.get('GOPHISH_PUBLIC_URL') or env['PHISH_PUBLIC_URL']}")
    print(f"     Recipient:    daniel.e@bottleking.ng only")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"GoPhish API error {exc.code}: {detail}") from exc

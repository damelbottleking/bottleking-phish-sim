#!/usr/bin/env python3
"""Send pilot campaign email directly via SMTP (bypasses GoPhish mailer bug)."""

import json
import re
import smtplib
import sqlite3
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

BASE = "https://127.0.0.1:3333"
TO = "daniel.e@bottleking.ng"
FROM_DISPLAY = "kingsley@bottleking.ng"
FROM_HEADER = ("Kingsley Edochie", "kingsley@bottleking.ng")
REPLY_TO = "kingsley@bottleking.ng"
SUBJECT = "STAFF WELFARE & INVESTMENT BENEFIT"

ROOT = Path(__file__).resolve().parents[1]


def campaign_url():
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("PHISH_PUBLIC_URL="):
                return line.split("=", 1)[1].strip()
    return "http://127.0.0.1:8090"


def api_key():
    conn = sqlite3.connect(ROOT / "gophish-bin" / "gophish.db")
    row = conn.execute("SELECT api_key FROM users WHERE username='admin'").fetchone()
    conn.close()
    return row[0]


def api_get(path):
    req = urllib.request.Request(
        BASE + path,
        headers={"Authorization": "Bearer {}".format(api_key())},
    )
    ctx = urllib.request.ssl._create_unverified_context()
    with urllib.request.urlopen(req, context=ctx) as resp:
        return json.loads(resp.read().decode())


def load_smtp():
    conn = sqlite3.connect(ROOT / "gophish-bin" / "gophish.db")
    row = conn.execute("SELECT host, username, password FROM smtp WHERE id=2").fetchone()
    conn.close()
    return row[0], row[1], row[2]


def get_tracking_url():
    campaigns = api_get("/api/campaigns/")
    campaign = next(c for c in campaigns if c["name"].startswith("BK Partner Update"))
    results = api_get("/api/campaigns/{}/results".format(campaign["id"]))
    if isinstance(results, dict):
        results = results.get("results", [])
    for result in results:
        if result.get("email") == TO:
            rid = result.get("id")
            base = campaign_url().rstrip("/")
            return "{}/?rid={}".format(base, rid)
    return campaign_url()


def main():
    templates = api_get("/api/templates/")
    template = next((t for t in templates if "Dangote IPO" in t["name"] or "Welfare" in t.get("subject", "")), templates[0])
    # Prefer local file for latest content
    local_tpl = ROOT / "templates" / "email-bottleking-update.html"
    if local_tpl.exists():
        html = local_tpl.read_text(encoding="utf-8")
    else:
        html = template["html"]
    url = get_tracking_url()
    html = html.replace("{{.URL}}", url)
    html = html.replace("{{.FirstName}}", "Daniel")
    base = campaign_url().rstrip("/")
    html = html.replace("{{.Tracker}}", "")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = SUBJECT
    msg["From"] = "{} <{}>".format(FROM_HEADER[0], FROM_HEADER[1])
    msg["Reply-To"] = REPLY_TO
    msg["To"] = TO
    msg.attach(MIMEText("Accept your BottleKing staff welfare benefit. Click the link to confirm your details.", "plain"))
    msg.attach(MIMEText(html, "html"))

    host, username, password = load_smtp()
    host_name, port = host.split(":")
    with smtplib.SMTP(host_name, int(port), timeout=30) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(username, password)
        # Envelope must match authenticated account unless Workspace "Send mail as" is enabled.
        server.sendmail(username, [TO], msg.as_string())

    print("Pilot email sent to {}".format(TO))
    print("Tracking link: {}".format(url))


if __name__ == "__main__":
    main()

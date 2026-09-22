#!/usr/bin/env python3
"""Send test email using stored GoPhish SMTP settings."""

import json
import smtplib
import sqlite3
import urllib.error
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://127.0.0.1:3333"
TEST_EMAIL = "daniel.e@bottleking.ng"
FROM_DISPLAY = "Kingsley Edochie <kingsley@bottleking.ng>"
ENVELOPE_FROM = "daniel.e@bottleking.ng"


def load_smtp():
    conn = sqlite3.connect(ROOT / "gophish-bin" / "gophish.db")
    row = conn.execute(
        "SELECT host, username, password FROM smtp WHERE id=2"
    ).fetchone()
    conn.close()
    if not row or not row[2]:
        raise SystemExit("SMTP password missing in GoPhish profile id=2")
    return row[0], row[1], row[2]


def send_direct(host, username, password):
    html = call_api_template_html()
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "After Dangote IPO, BK update!!!"
    msg["From"] = FROM_DISPLAY
    msg["To"] = TEST_EMAIL
    msg.attach(MIMEText("Please view the partnership acknowledgment form.", "plain"))
    msg.attach(MIMEText(html, "html"))

    host_name, port = host.split(":")
    port = int(port)
    with smtplib.SMTP(host_name, port, timeout=30) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(username, password)
        server.sendmail(ENVELOPE_FROM, [TEST_EMAIL], msg.as_string())
    print("SUCCESS: direct SMTP send to {}".format(TEST_EMAIL))


def api_key():
    conn = sqlite3.connect(ROOT / "gophish-bin" / "gophish.db")
    row = conn.execute("SELECT api_key FROM users WHERE username='admin'").fetchone()
    conn.close()
    return row[0]


def call_api_template_html():
    req = urllib.request.Request(
        BASE + "/api/templates/",
        headers={"Authorization": "Bearer {}".format(api_key())},
    )
    ctx = urllib.request.ssl._create_unverified_context()
    with urllib.request.urlopen(req, context=ctx) as resp:
        templates = json.loads(resp.read().decode())
    template = next(t for t in templates if t["name"] == "After Dangote IPO BK Update")
    return template.get("html", "<p>BottleKing test email</p>")


def send_via_gophish_api():
    profiles = api_get("/api/smtp/")
    smtp = next(p for p in profiles if p["id"] == 2)
    smtp["from_address"] = FROM_DISPLAY
    smtp["headers"] = []
    password = smtp.get("password")
    if not password:
        _, _, password = load_smtp()
    smtp["password"] = password

    payload = {
        "template": {},
        "first_name": "Daniel",
        "last_name": "Ekundayo",
        "email": TEST_EMAIL,
        "position": "Tech",
        "url": "http://127.0.0.1:8090",
        "smtp": smtp,
    }
    api_post("/api/util/send_test_email", payload)
    print("SUCCESS: GoPhish test email API sent to {}".format(TEST_EMAIL))


def api_get(path):
    req = urllib.request.Request(
        BASE + path,
        headers={"Authorization": "Bearer {}".format(api_key())},
    )
    ctx = urllib.request.ssl._create_unverified_context()
    with urllib.request.urlopen(req, context=ctx) as resp:
        return json.loads(resp.read().decode())


def api_post(path, body):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode(),
        headers={
            "Authorization": "Bearer {}".format(api_key()),
            "Content-Type": "application/json",
        },
        method="POST",
    )
    ctx = urllib.request.ssl._create_unverified_context()
    with urllib.request.urlopen(req, context=ctx) as resp:
        return json.loads(resp.read().decode())


def main():
    host, username, password = load_smtp()
    print("Using SMTP user: {}".format(username))
    try:
        send_direct(host, username, password)
        return
    except smtplib.SMTPException as exc:
        print("Direct SMTP failed: {}".format(exc))
        print("Trying GoPhish API path...")

    try:
        send_via_gophish_api()
    except urllib.error.HTTPError as exc:
        print(exc.read().decode())
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()

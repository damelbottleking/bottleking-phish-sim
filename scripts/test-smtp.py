#!/usr/bin/env python3
"""Quick SMTP test — run locally with your App Password (never commit it)."""

import getpass
import smtplib
import sys
from email.mime.text import MIMEText


def main() -> None:
    username = input("Your @bottleking.ng email: ").strip()
    password = getpass.getpass("Google App Password (16 chars, no spaces): ").strip().replace(" ", "")
    to_addr = input("Send test to [daniel.e@bottleking.ng]: ").strip() or "daniel.e@bottleking.ng"

    msg = MIMEText("BottleKing SMTP test — if you got this, sending works.")
    msg["Subject"] = "SMTP Test"
    msg["From"] = f"Kingsley Edochie <kingsley@bottleking.ng>"
    msg["To"] = to_addr

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(username, password)
            server.sendmail(username, [to_addr], msg.as_string())
    except smtplib.SMTPAuthenticationError as exc:
        print("\nFAILED: Google rejected login.")
        print("Use an App Password, NOT your normal Google password.")
        print("Create one at: Google Account -> Security -> App passwords")
        print(f"Detail: {exc}")
        sys.exit(1)
    except Exception as exc:
        print(f"\nFAILED: {exc}")
        sys.exit(1)

    print(f"\nSUCCESS: Test email sent to {to_addr}")


if __name__ == "__main__":
    main()

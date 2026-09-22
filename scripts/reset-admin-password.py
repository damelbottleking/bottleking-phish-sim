#!/usr/bin/env python3
"""Reset GoPhish admin password in the local SQLite database."""

import sqlite3
import sys
from pathlib import Path

try:
    import bcrypt
except ImportError:
    import subprocess

    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "bcrypt"])
    import bcrypt

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "gophish-bin" / "gophish.db"
NEW_PASSWORD = "BottleKing2026!"


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(f"Database not found: {DB_PATH}")

    hashed = bcrypt.hashpw(NEW_PASSWORD.encode("utf-8"), bcrypt.gensalt(rounds=10))
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE users SET hash = ?, password_change_required = 0, account_locked = 0 WHERE username = 'admin'",
        (hashed.decode("utf-8"),),
    )
    conn.commit()
    conn.close()

    login_file = ROOT / "ADMIN-LOGIN.txt"
    login_file.write_text(
        "\n".join(
            [
                "GoPhish Admin Login (local)",
                "============================",
                "URL:      https://127.0.0.1:3333",
                "Username: admin",
                f"Password: {NEW_PASSWORD}",
                "",
                "Landing page (local test): http://127.0.0.1:8080",
                "Tracker health:            http://127.0.0.1:9090/health",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(f"Admin password reset to: {NEW_PASSWORD}")
    print(f"Saved to: {login_file}")


if __name__ == "__main__":
    main()

# BottleKing Phishing Simulation (GoPhish)

Internal security awareness setup for Google Workspace.

Tracks three groups:

1. **Clicked** the email link
2. **Partial fill** — clicked and interacted with the form, did not submit
3. **Submitted** — clicked, filled the form, and submitted

## Before you start

- Get written approval from IT/security leadership and HR.
- Use only for authorized internal training.
- Do not store or reuse real employee passwords.

## Project layout

```
bottleking-phish-sim/
├── gophish-bin/          # GoPhish binary (local Mac)
├── gophish/config.json   # GoPhish server config
├── tracker/              # Partial form interaction tracker
├── templates/            # Email + landing page HTML
├── data/                 # Staff CSV + exported results
├── scripts/              # Start/stop/export helpers
└── docs/                 # Google Workspace SMTP guide
```

## Quick start (local Mac)

```bash
cd ~/Documents/bottleking-phish-sim
cp .env.example .env
# Edit .env with kingsley@bottleking.ng SMTP details

bash scripts/start.sh
```

1. Open `https://127.0.0.1:3333`
2. Accept the self-signed certificate warning
3. Log in with `admin` and the one-time password printed in the terminal
4. Change the admin password immediately

## Configure GoPhish (one time)

### Sending profile

See [docs/google-workspace-smtp.md](docs/google-workspace-smtp.md).

Use From: `Kingsley <kingsley@bottleking.ng>`.

### Email template

Replace `templates/email-template-placeholder.html` with your real template, then:

```bash
bash scripts/prepare-templates.sh
```

Paste `templates/prepared/email-template-ready.html` into GoPhish.

### Landing page

```bash
bash scripts/prepare-templates.sh
```

Paste `templates/prepared/landing-page-ready.html` into GoPhish.

Landing page settings:

- Capture credentials: **On**
- Capture passwords: **Off** (recommended — only record submission event)
- Redirect to: your training page or `https://bottleking.ng`

### User group

1. GoPhish -> Users & Groups -> New Group
2. Import your staff CSV (same format as `data/staff-import-template.csv`)

```csv
First Name,Last Name,Email,Position
```

## Launch a campaign

1. Campaigns -> New Campaign
2. Name: match `CAMPAIGN_NAME` in `.env`
3. Email template: your imported template
4. Landing page: BottleKing login page
5. URL: public phishing URL (e.g. `https://phish.bottleking.ng`)
6. Sending profile: BottleKing SMTP
7. Groups: all staff
8. Send or schedule

## Export the 3 email lists

After the campaign runs:

1. GoPhish -> Settings -> copy API key into `.env` as `GOPHISH_API_KEY`
2. Run:

```bash
python3 scripts/export-results.py
```

Output:

- `data/exports/1-clicked.csv`
- `data/exports/2-partial-fill.csv`
- `data/exports/3-submitted.csv`

## Production (Linux server + Docker)

```bash
docker compose up -d --build
```

Point DNS `phish.bottleking.ng` to the server. Nginx routes:

- `/` -> GoPhish landing pages
- `/track` -> interaction tracker

Admin UI stays on port `3333` (restrict access by firewall/VPN).

## What to send next

When ready, provide:

1. Your HTML email template
2. Staff email CSV

Then we import them and launch the pilot campaign.

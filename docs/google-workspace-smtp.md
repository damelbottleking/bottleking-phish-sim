# Google Workspace SMTP for GoPhish

Use a dedicated sender like `kingsley@bottleking.ng` for the simulation.

## 1. Create a Google App Password

Google Workspace will not allow normal account passwords for SMTP in most setups.

1. Sign in to the sender account (`kingsley@bottleking.ng`).
2. Enable 2-Step Verification on the account.
3. Open Google Account -> Security -> App passwords.
4. Create an app password for "Mail".
5. Copy the 16-character password into `.env` as `SMTP_PASSWORD`.

## 2. GoPhish sending profile

In GoPhish admin (`https://127.0.0.1:3333`):

| Field | Value |
|-------|-------|
| Name | BottleKing SMTP |
| From | Kingsley `<kingsley@bottleking.ng>` |
| Host | `smtp.gmail.com:587` |
| Username | `kingsley@bottleking.ng` |
| Password | App password from step 1 |
| Ignore Certificate Errors | No |

Use **Send Test Email** before launching the campaign.

## 3. Deliverability tips

- Send from a real company mailbox, not a random alias.
- Run a small pilot (5-10 users) before full broadcast.
- Ask IT to allowlist the sending account if messages land in spam.
- Keep the From name consistent with your template.

## 4. Public phishing URL

Staff must reach your landing page when they click the email.

For production, use a subdomain such as:

- `https://phish.bottleking.ng` -> forwards to GoPhish port 8080
- `https://phish.bottleking.ng/track` -> forwards to tracker port 9090

For local testing, expose ports with ngrok or Cloudflare Tunnel and set:

- `PHISH_PUBLIC_URL`
- `TRACKER_PUBLIC_URL`

in `.env`, then run `bash scripts/prepare-templates.sh`.

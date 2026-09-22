# IT account sending as Kingsley

GoPhish uses two different things:

| Setting | Purpose | Example |
|---------|---------|---------|
| **From** | What staff see in their inbox | `Kingsley Edochie <kingsley@bottleking.ng>` |
| **SMTP Username** | Your IT account that logs in to send | `you@bottleking.ng` or `security@bottleking.ng` |
| **SMTP Password** | That IT account's Google App Password | 16-character app password |

You do **not** need Kingsley's mailbox password.

## Best setup (cleanest "from Kingsley" look)

Ask your Google Workspace admin to:

1. Create or use an IT/security mailbox for simulations
2. Grant that mailbox **"Send mail as"** permission for `kingsley@bottleking.ng`

Then in GoPhish **Sending Profiles**:

- **From:** `Kingsley Edochie <kingsley@bottleking.ng>`
- **Host:** `smtp.gmail.com:587`
- **Username:** your IT mailbox
- **Password:** IT mailbox App Password

## Minimum setup (works without admin help)

Use **your own** `@bottleking.ng` IT account:

1. Enable 2-Step Verification on your account
2. Create a Google App Password for Mail
3. Enter it in GoPhish under **Sending Profiles**

The email may show a small **"via your-account@bottleking.ng"** line in some clients if "Send mail as" was not configured. The main From name will still show Kingsley.

## In GoPhish UI

1. Open https://127.0.0.1:3333
2. **Sending Profiles** → **BottleKing IT Send (From Kingsley)**
3. Set **Username** to your IT `@bottleking.ng` account
4. Paste your **App Password**
5. Keep **From** as `Kingsley Edochie <kingsley@bottleking.ng>`
6. **Send Test Email** to `daniel.e@bottleking.ng`

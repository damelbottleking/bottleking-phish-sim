# Campaign checklist

Use this before sending to all staff.

## Authorization

- [ ] Security/IT leadership approved the exercise
- [ ] HR/legal aware of employee notification policy
- [ ] Debrief/training plan ready for people who click or submit

## Infrastructure

- [ ] GoPhish admin password changed from default
- [ ] Sender account configured: `kingsley@bottleking.ng`
- [ ] Google App Password created and saved in `.env`
- [ ] Test email delivered successfully
- [ ] Public URL reachable from outside office network
- [ ] Landing page loads at campaign URL
- [ ] Tracker health check: `/health` returns OK

## GoPhish objects

- [ ] Sending profile: BottleKing SMTP
- [ ] Email template imported
- [ ] Landing page imported (capture passwords OFF)
- [ ] User group imported from staff CSV
- [ ] Campaign name matches `CAMPAIGN_NAME` in `.env`

## Pilot first

- [ ] Send to 5-10 test users
- [ ] Confirm click tracking works
- [ ] Confirm partial fill tracking works (type in form, don't submit)
- [ ] Confirm submit tracking works
- [ ] Run `python3 scripts/export-results.py` on pilot

## Full broadcast

- [ ] Schedule or send campaign
- [ ] Monitor bounce/spam issues
- [ ] Export final 3 CSV lists after campaign window closes

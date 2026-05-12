# 011_alert_bottleneck_escalation

Daily 8 AM PHT cron. Lists applicants stuck in Stage 10 (Passed Assessment)
for over 48 hours and digests them to the HR Recruitment Manager group.

| Kind | xml_id |
|---|---|
| Server action | `bicc_recruitment.bottleneck_escalation` |
| Cron | `bicc_recruitment.cron_bottleneck_escalation` — every 1 day, nextcall `2026-05-13 00:00:00` (8 AM PHT) |

## QA on dev

1. Settings → Technical → Scheduled Actions → `BICC v5: Bottleneck Escalation (daily)` → Run Manually.
2. If any active applicants are sitting in Stage 10 with `write_date > 48h ago`, HR Recruitment Manager users get an inbox digest.
3. No stagnant candidates → silent no-op (logs `nothing to send`).

## Notes

- Pure procedural — no nested defs, no closures, no captured genexps.
- Refactored from the original `alert_bottleneck_escalation.py`: notification
  recipient list is built via an explicit for-loop instead of the
  `[(4, p) for p in notify_partners.ids]` comprehension. Functionally
  identical; written this way as a defensive habit against safe_eval's
  closure rules.

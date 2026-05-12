# 012_alert_daily_n8n_retry

Daily 2 AM PHT cron. Lists applicants stuck in Stage 1 (New) for > 24h.

| Kind | xml_id |
|---|---|
| Server action | `bicc_recruitment.daily_n8n_retry` |
| Cron | `bicc_recruitment.cron_daily_n8n_retry` — every 1 day, nextcall `2026-05-12 18:00:00` (= 2 AM PHT) |

## QA on dev

Run the SA manually from Settings → Technical → Server Actions. Stuck
applicants (Stage 1, create_date > 24h ago) get a chatter line. HR
Recruitment Manager group gets a digest email.

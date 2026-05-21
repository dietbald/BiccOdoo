# 019_test_recruitment_fixtures

Two server actions that create and reset deterministic `hr.applicant`
test fixtures so the recruitment automation pipeline can be validated
end-to-end without touching real applicant data.

## Ships

- **BICC TEST: Seed Recruitment Fixtures** — Action menu on Applicants
  (form + list). Creates 6 fixture applicants with unique Mailinator
  emails. Idempotent — re-run to reset all 6 to a clean starting
  state.
- **BICC TEST: Reset Recruitment Fixtures** — Action menu on Applicants
  (form + list). Archives all `TEST_FIXTURE_*` rows and unlinks the
  seeded `survey.user_input` records.

## Production guard

The seed SA reads `web.base.url`. If it contains `bicc.odoo.com`
without a `dev`/`ph2`/`staging` marker, it raises a UserError. The
reset SA is unguarded (it's keyed by the `TEST_FIXTURE_` name prefix,
which no real applicant uses).

So even if this changeset gets promoted to prod by accident, the seed
button is harmless. The intended deployment is dev + staging only.

## Fixtures created

Each gets a Mailinator inbox at `bicc-fixture-<suffix>@mailinator.com`
that you can read in a browser to verify the right emails fired.

| Name | Stage | Backdated 3d | Notes |
|---|---|---|---|
| `TEST_FIXTURE_STAGE1_NORESUME_FRESH` | New (1) | no | Used to verify 005 resume gate (manual UI test — apply via portal) |
| `TEST_FIXTURE_STAGE1_NORESUME_OLD` | New (1) | yes | Used to verify 009 SMS-flagging path for Stage 1 |
| `TEST_FIXTURE_STAGE2_NOSURVEY_FRESH` | Qualification (2) | no | Used to verify 006 info dispatch fires on stage entry |
| `TEST_FIXTURE_STAGE2_NOSURVEY_OLD` | Qualification (2) | yes | Used to verify 009 reminder cascade (first reminder) |
| `TEST_FIXTURE_STAGE7_PARTIAL_OLD` | Assessment Sent (7) | yes | 1 of 3 assessments done — verifies 010 lists Logical + Emotional in the reminder email |
| `TEST_FIXTURE_STAGE7_NODONE_OLD` | Assessment Sent (7) | yes | 0 of 3 done — verifies 010 lists all three |

## Prerequisites on the env

The seed SA needs at least one active `hr.job` with all four survey
fields populated:
- `x_studio_application_information`
- `survey_id` (Technical assessment)
- `x_studio_logical_assessment`
- `x_studio_emotional_assessment`

If none exists it raises a UserError naming the missing fields.

## What's NOT seeded (and why)

`scoring_success` is a stored computed field on `survey.user_input`
driven by the actual survey scoring engine — it can't be set via API.
So the pass/fail branches of 007 (info-survey adjudication) and 010
(triple-assessment pass/fail) need a real browser walk-through:

1. Open the per-applicant survey URL in an incognito tab
2. Answer the questions correctly/incorrectly
3. Submit
4. Watch the SA fire on the resulting `state='done'` transition

## QA flow (after deploy)

1. Settings → Technical → Actions → Server Actions → "BICC TEST: Seed Recruitment Fixtures" → Run
2. Kanban opens filtered to the 6 fixtures
3. Settings → Technical → Scheduled Actions → `BICC v5: Janitor Track 1 (daily)` → **Run Manually**
4. Open Mailinator `bicc-fixture-stage2_nosurvey_old@mailinator.com` — confirm the General Follow-up Reminder arrived
5. `BICC v5: Janitor Track 2 (daily)` → **Run Manually**
6. Open Mailinator `bicc-fixture-stage7_partial_old@mailinator.com` — confirm the email lists `Logical` + `Emotional` links (NOT Technical)
7. Open Mailinator `bicc-fixture-stage7_nodone_old@mailinator.com` — confirm the email lists all 3
8. Reset SA → all 6 archived, all seeded inputs deleted

## Rollback

Block rollback deletes both SAs. Already-seeded fixtures remain in
the DB but archived; run reset before rollback for a clean wipe.

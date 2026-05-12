# 007_info_survey_adjudication

Info-survey verdict gate. Fires when the survey is submitted.

| Kind | xml_id |
|---|---|
| Template | `bicc_recruitment.tpl_info_survey_failure` |
| Server action | `bicc_recruitment.info_survey_adjudication` (model `survey.user_input`) |
| Automation | `bicc_recruitment.automation_info_survey_adjudication` (on `survey.user_input.on_write`) |

## Behaviour

- **Fail** (`scoring_success == False`): during PHT office hours (Mon–Sat
  10–17, no holiday) → archive applicant + send failure-score email.
  Off hours → flag `kanban_state='blocked'` and set
  `x_studio_queued_refusal_id` so the Track-1 janitor (changeset 009)
  drains the refusal in the morning.
- **Pass** (`scoring_success == True`): advance applicant to Stage 7
  (Assessment Sent). No priority bumping — Star Talent is decided
  exclusively by changeset 004 (Logical + Technical gate).
- **Zombie recovery**: if the matching applicant was already archived,
  re-activate them.

## QA on dev

1. Submit a failing info survey via public token URL → during PHT office
   hours, matching applicant is archived + failure email queued. Off
   hours → applicant flagged `kanban_state=blocked` +
   `x_studio_queued_refusal_id` set; the Track-1 janitor will finish the
   refusal at 8 AM PHT.
2. Submit a passing info survey → applicant jumps to Stage 7. No star
   tag here.

## Notes

- The info survey is not a scored survey in BICC's current setup
  (`scoring_type='no_scoring'`). Odoo computes `scoring_percentage=0`
  and `scoring_success=True` for non-scored user_inputs, so in practice
  every completed info survey advances the applicant to Stage 7 and the
  "fail" branch never fires. The branch is left in place because the
  info survey could be made scored in the future.
- Coexists with changeset 004 (Star Talent Alert), which also fires on
  `survey.user_input.on_write`. The two automations run independently.

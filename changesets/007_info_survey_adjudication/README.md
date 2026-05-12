# 007_info_survey_adjudication

Info-survey verdict gate. Fires when the survey is submitted.

| Kind | xml_id |
|---|---|
| Template | `bicc_recruitment.tpl_info_survey_failure` |
| Server action | `bicc_recruitment.info_survey_adjudication` (model `survey.user_input`) |
| Automation | `bicc_recruitment.automation_info_survey_adjudication` (on `survey.user_input.on_write`) |

## QA on dev

1. Submit a failing info survey via public token URL → during PHT office hours,
   matching applicant is archived + failure email queued. Off hours → applicant
   flagged `kanban_state=blocked` + `x_studio_queued_refusal_id` set.
2. Submit a high-scoring (≥ 90%) survey → applicant jumps to Stage 7 with
   `priority=3` (★★★) and a "STAR TALENT" chatter line.

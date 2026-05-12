# TRIGGER: survey.user_input on_write (only fires the alert once we
#   re-check the dual-gate inside).
# MODEL: survey.user_input
# DESCRIPTION: Alert recruiter on Star Candidates. Rule:
#   - Applicant has completed BOTH the Logical AND the Technical
#     assessment for their job.
#   - Logical score >= LOGICAL_THRESHOLD (90%)
#   - Technical score >= TECHNICAL_THRESHOLD (80%)
#   Effect: priority bumped to ★★★ (priority='3') + chatter alert tagging
#   the assigned recruiter so they get an inbox notification.
#
# Pure procedural — no closures.

LOGICAL_THRESHOLD = 90.0
TECHNICAL_THRESHOLD = 80.0

# Resolve the matching applicant (most recent if duplicate emails)
applicant = env['hr.applicant'].search(
    [('email_from', '=', record.email)],
    limit=1, order='id desc',
)

if applicant and applicant.job_id and record.survey_id:
    job = applicant.job_id
    tech_survey = job.survey_id                   # native: Technical assessment
    logi_survey = job.x_studio_logical_assessment # Studio: Logical assessment

    # Bail unless the survey just written is the Technical OR Logical for
    # this applicant's job — keeps emotional/info-survey writes from
    # re-triggering the alert.
    is_relevant = False
    if tech_survey and record.survey_id.id == tech_survey.id:
        is_relevant = True
    if logi_survey and record.survey_id.id == logi_survey.id:
        is_relevant = True

    if is_relevant:
        # Pull the applicant's most-recent done input for each survey
        tech_input = env['survey.user_input']
        logi_input = env['survey.user_input']
        if tech_survey:
            tech_input = env['survey.user_input'].search([
                ('email', '=', record.email),
                ('survey_id', '=', tech_survey.id),
                ('state', '=', 'done'),
            ], limit=1, order='id desc')
        if logi_survey:
            logi_input = env['survey.user_input'].search([
                ('email', '=', record.email),
                ('survey_id', '=', logi_survey.id),
                ('state', '=', 'done'),
            ], limit=1, order='id desc')

        # Only proceed once BOTH assessments are done
        if tech_input and logi_input:
            tech_score = tech_input.scoring_percentage or 0.0
            logi_score = logi_input.scoring_percentage or 0.0

            if (logi_score >= LOGICAL_THRESHOLD and
                    tech_score >= TECHNICAL_THRESHOLD):
                # Dedup: if already flagged star, don't re-alert
                if applicant.priority != '3':
                    applicant.write({'priority': '3'})

                    notify_ids = []
                    if applicant.user_id and applicant.user_id.partner_id:
                        notify_ids = [applicant.user_id.partner_id.id]

                    job_name = applicant.job_id.name or 'their role'
                    applicant.message_post(
                        body=(
                            "STAR CANDIDATE ALERT: %s scored Logical %.1f%% "
                            "+ Technical %.1f%% for %s. Call them immediately."
                        ) % (applicant.partner_name or 'Unknown',
                             logi_score, tech_score, job_name),
                        subtype_xmlid="mail.mt_comment",
                        partner_ids=notify_ids,
                    )
                    applicant.message_post(
                        body="MANAGEMENT: High-priority alert dispatched to recruiter (Logical+Technical gate).")

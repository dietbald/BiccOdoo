# TRIGGER: When any survey.user_input state becomes 'done' AND score ≥ 90%
# MODEL: survey.user_input
# DESCRIPTION: Instant high-priority alert for star candidates. Bumps
#   applicant priority to ★★★ and pings the assigned recruiter via a
#   tagged chatter post on the applicant record so they get an inbox
#   notification immediately.

STAR_THRESHOLD = 90.0

applicant = env['hr.applicant'].search(
    [('email_from', '=', record.email)],
    limit=1, order='id desc',
)

if applicant and (record.scoring_percentage or 0.0) >= STAR_THRESHOLD:
    applicant.write({'priority': '3'})

    survey_title = record.survey_id.title if record.survey_id else 'a survey'
    job_name = applicant.job_id.name if applicant.job_id else 'their role'

    notify_ids = []
    if applicant.user_id and applicant.user_id.partner_id:
        notify_ids = [applicant.user_id.partner_id.id]

    applicant.message_post(
        body=(
            "<b>STAR CANDIDATE ALERT:</b> %s scored %.1f%% on %s for %s. "
            "<b>Call them immediately!</b>"
        ) % (applicant.partner_name or 'Unknown',
             record.scoring_percentage or 0.0,
             survey_title,
             job_name),
        subtype_xmlid="mail.mt_comment",
        partner_ids=notify_ids,
    )
    applicant.message_post(body="MANAGEMENT: High-priority alert dispatched to recruiter.")

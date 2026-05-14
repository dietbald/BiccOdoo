# TRIGGER: Scheduled Action (Daily, 8 AM PHT)
# MODEL: hr.applicant
# DESCRIPTION: Track 2 janitor for Stage 7 (Assessment Sent) applicants.
#   - Identifies which of the 3 assessments are still incomplete (reusing
#     existing state='new' survey.user_input rows rather than creating
#     fresh ones every cron run).
#   - If any missing → stamp the pending-links HTML into a scratch field
#     on the applicant and send a dedicated assessment-reminder template
#     that renders that field inline (general → final → archive).
#   - If all done → check scoring_success: any failed → kanban_state=
#     blocked + REVIEW NEEDED chatter; all passed → advance to Stage 10.
#
# Pure procedural — no nested defs, no genexp closures.

STAGE_ASSESSMENT_SENT = 7
STAGE_PASSED_ASSESSMENT = 10
TPL_ASSESSMENT_GENERAL = 'Recruitment: Assessment Reminder (Partial Bundle)'
TPL_ASSESSMENT_FINAL = 'Recruitment: Final Assessment Reminder Before Archive'
TPL_NON_RESPONSE = 'Recruitment: Refuse did not complete assessment'
REMINDER_INTERVAL_HOURS = 48

now = datetime.datetime.now()
cutoff = now - datetime.timedelta(hours=REMINDER_INTERVAL_HOURS)

track2 = env['hr.applicant'].search([
    ('active', '=', True),
    ('stage_id', '=', STAGE_ASSESSMENT_SENT),
])

for rec in track2:
    if not (rec.email_from or '').strip():
        continue

    # Compute last action date (most recent reminder, fallback stage change)
    candidate_dates = []
    if rec.x_studio_assessment_reminder_date:
        candidate_dates.append(rec.x_studio_assessment_reminder_date)
    if rec.x_studio_assessment_final_reminder_date:
        candidate_dates.append(rec.x_studio_assessment_final_reminder_date)
    if candidate_dates:
        last_date = candidate_dates[0]
        for d in candidate_dates[1:]:
            if d > last_date:
                last_date = d
    else:
        last_date = rec.date_last_stage_update

    if last_date and last_date > cutoff:
        continue

    recent_activity = env['survey.user_input'].search_count([
        ('email', '=', rec.email_from),
        ('write_date', '>', cutoff.strftime('%Y-%m-%d %H:%M:%S')),
    ])
    if recent_activity > 0:
        continue

    # Detect missing assessments. Use a small per-job list so we can iterate
    # without a nested helper / comprehension (safe_eval rules).
    job = rec.job_id
    done_inputs = env['survey.user_input'].search([
        ('email', '=', rec.email_from),
        ('state', '=', 'done'),
    ])
    done_ids = done_inputs.mapped('survey_id.id')

    surveys_to_check = []
    if job and job.survey_id:
        surveys_to_check.append(('Technical', job.survey_id))
    if job and job.x_studio_logical_assessment:
        surveys_to_check.append(('Logical', job.x_studio_logical_assessment))
    if job and job.x_studio_emotional_assessment:
        surveys_to_check.append(('Emotional', job.x_studio_emotional_assessment))

    missing_links = []
    for label, survey in surveys_to_check:
        if survey.id in done_ids:
            continue
        # Reuse an existing state='new' user_input for (this email, this
        # survey) if present — only mint a new one when none exists.
        ui = env['survey.user_input'].search([
            ('survey_id', '=', survey.id),
            ('email', '=', rec.email_from),
            ('state', '=', 'new'),
        ], limit=1)
        if not ui:
            ui = env['survey.user_input'].create({
                'survey_id': survey.id,
                'email': rec.email_from,
                'state': 'new',
            })
        u = ui.get_start_url()
        missing_links.append("<li><b>%s:</b> <a href='%s'>%s</a></li>" % (label, u, u))

    if not missing_links:
        # All assessments completed — check pass/fail
        job_survey_ids = []
        if job and job.survey_id:
            job_survey_ids.append(job.survey_id.id)
        if job and job.x_studio_logical_assessment:
            job_survey_ids.append(job.x_studio_logical_assessment.id)
        if job and job.x_studio_emotional_assessment:
            job_survey_ids.append(job.x_studio_emotional_assessment.id)

        completed_for_job = env['survey.user_input'].search([
            ('email', '=', rec.email_from),
            ('state', '=', 'done'),
            ('survey_id', 'in', job_survey_ids),
        ])
        failed_titles = []
        for inp in completed_for_job:
            if inp.survey_id.scoring_type != 'no_scoring' and not inp.scoring_success:
                failed_titles.append(inp.survey_id.title)

        if failed_titles:
            rec.write({'kanban_state': 'blocked'})
            rec.message_post(body=(
                "REVIEW NEEDED: All assessments completed but FAILED: %s. "
                "HR must decide whether to refuse or advance."
            ) % ', '.join(failed_titles))
        else:
            rec.write({'stage_id': STAGE_PASSED_ASSESSMENT})
            rec.message_post(body="AUTOMATION: All assessments completed and passed. Moving to Passed Assessment stage.")
        continue

    # Missing items — stamp scratch field then cascade reminders.
    links_html = "<ul>" + "".join(missing_links) + "</ul>"
    rec.write({'x_studio_assessment_pending_links': links_html})

    reminder_date = rec.x_studio_assessment_reminder_date
    final_date = rec.x_studio_assessment_final_reminder_date

    if not reminder_date:
        tpl = env['mail.template'].search([('name', '=', TPL_ASSESSMENT_GENERAL)], limit=1)
        if not tpl.exists():
            rec.message_post(body="AUTOMATION ERROR: Template '%s' not found — assessment reminder skipped." % TPL_ASSESSMENT_GENERAL)
            continue
        tpl.send_mail(rec.id, force_send=False)
        rec.write({'x_studio_assessment_reminder_date': now})
    elif not final_date:
        tpl = env['mail.template'].search([('name', '=', TPL_ASSESSMENT_FINAL)], limit=1)
        if not tpl.exists():
            rec.message_post(body="AUTOMATION ERROR: Template '%s' not found — final assessment reminder skipped." % TPL_ASSESSMENT_FINAL)
            continue
        tpl.send_mail(rec.id, force_send=False)
        rec.write({
            'x_studio_assessment_final_reminder_date': now,
            'x_studio_assessment_sms_reminder_date': False,
        })
    else:
        tpl = env['mail.template'].search([('name', '=', TPL_NON_RESPONSE)], limit=1)
        if not tpl.exists():
            rec.message_post(body="AUTOMATION ERROR: Template '%s' not found — archiving without farewell email." % TPL_NON_RESPONSE)
        else:
            tpl.send_mail(rec.id, force_send=False)
        rec.write({'active': False})
        rec.message_post(body="AUTOMATION: Auto-archived after unanswered Track 2 reminders.")

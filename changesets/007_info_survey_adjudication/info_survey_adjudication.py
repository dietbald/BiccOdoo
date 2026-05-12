# TRIGGER: survey.user_input on_write of state (when it becomes 'done')
# MODEL: survey.user_input
# DESCRIPTION: Info-survey verdict gate.
#   - scoring_success False → auto-archive with failure email (office hours)
#     or queue refusal in x_studio_queued_refusal_id (off hours).
#   - scoring_success True → advance applicant to Stage 7; priority=high
#     if score ≥ 90 (Star Talent).
#   - Zombie recovery: re-activate archived applicants if their survey
#     comes in.

STAGE_ASSESSMENT_SENT = 7
TPL_SCORE_FAILURE = 'Recruitment: Info Survey Below Passing Score'
SCORE_STAR = 90.0

# PHT office hours gate (no pytz in safe_eval; use fixed UTC+8 offset)
now_utc = datetime.datetime.now()
PHT = datetime.timezone(datetime.timedelta(hours=8))
now_pht = datetime.datetime.now(PHT)
is_working_hours = (10 <= now_pht.hour < 17) and (now_pht.weekday() != 6)
is_holiday = env['resource.calendar.leaves'].search_count([
    ('date_from', '<=', now_utc),
    ('date_to', '>=', now_utc),
    ('resource_id', '=', False),
]) > 0
can_send_refusal = is_working_hours and not is_holiday

# Match applicant by (email + their job's info-survey)
applicant = env['hr.applicant'].with_context(active_test=False).search([
    ('email_from', '=', record.email),
    ('job_id.x_studio_application_information', '=', record.survey_id.id),
], limit=1, order='id desc')

if applicant:
    # Zombie recovery
    if not applicant.active:
        applicant.write({'active': True})
        applicant.message_post(body="QA RECOVERY: Archived applicant completed survey. Restoring to pipeline.")

    if not record.scoring_success:
        # FAIL — auto-refuse or queue
        score_pct = record.scoring_percentage or 0.0
        if can_send_refusal:
            tpl = env['mail.template'].search([('name', '=', TPL_SCORE_FAILURE)], limit=1)
            if tpl.exists():
                tpl.send_mail(applicant.id, force_send=False)
            else:
                applicant.message_post(body="AUTOMATION ERROR: Template '%s' not found." % TPL_SCORE_FAILURE)
            applicant.write({'active': False})
            applicant.message_post(body=(
                "AUTOMATION: Refused - info survey did not pass "
                "(scoring_success=False, score=%.1f%%)."
            ) % score_pct)
        else:
            applicant.write({
                'x_studio_queued_refusal_id': TPL_SCORE_FAILURE,
                'kanban_state': 'blocked',
            })
            applicant.message_post(body=(
                "AUTOMATION: Info survey failure queued (outside office hours). Score=%.1f%%."
            ) % score_pct)
    else:
        # PASS — advance + maybe star
        score_pct = record.scoring_percentage or 0.0
        vals = {'stage_id': STAGE_ASSESSMENT_SENT}
        if score_pct >= SCORE_STAR:
            vals['priority'] = '3'
            applicant.message_post(body=(
                "STAR TALENT: Info survey score %.1f%% - marked as high priority."
            ) % score_pct)
        applicant.write(vals)
        applicant.message_post(body=(
            "AUTOMATION: Passed info screening (%.1f%%). Moving to Assessment stage."
        ) % score_pct)

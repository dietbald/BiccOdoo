# TRIGGER: survey.user_input on_write of state (when it becomes 'done')
# MODEL: survey.user_input
# DESCRIPTION: Info-survey verdict gate.
#   - scoring_success False → auto-archive with failure email (office hours)
#     or queue the refusal in x_studio_queued_refusal_id (off hours).
#   - scoring_success True → advance applicant to Stage 7.
#   - Zombie recovery: re-activate archived applicants if their survey
#     comes in.
#
#   Star-talent priority bumping is NOT done here — that lives in 004
#   (which uses the logical + technical assessment scores). The info
#   survey is not a scored survey, so the old "score >= 90 → priority=3"
#   path never fired anyway. Removed for clarity.

STAGE_ASSESSMENT_SENT = 7
TPL_SCORE_FAILURE = 'Recruitment: Info Survey Below Passing Score'

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
    # Zombie recovery — survey may arrive after applicant got archived
    if not applicant.active:
        applicant.write({'active': True})
        applicant.message_post(body="QA RECOVERY: Archived applicant completed survey. Restoring to pipeline.")

    if not record.scoring_success:
        # FAIL — auto-refuse during office hours, queue otherwise
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
        # PASS — advance to Stage 7. No priority bump here; star talent
        # is decided exclusively by 004 (logical + technical gate).
        applicant.write({'stage_id': STAGE_ASSESSMENT_SENT})
        applicant.message_post(body="AUTOMATION: Info screening complete. Moving to Assessment stage.")

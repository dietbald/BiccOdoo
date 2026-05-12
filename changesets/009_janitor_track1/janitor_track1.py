# TRIGGER: Scheduled Action (Daily, 8 AM PHT)
# MODEL: hr.applicant
# DESCRIPTION: Two responsibilities:
#   1. Drain the queued-refusal queue (applicants Block 04 / changeset 007
#      flagged off-hours): send the queued template and archive them.
#   2. For Stage 1 / Stage 2 applicants who haven't completed Survey 1,
#      cascade reminders 48h+ apart:
#         - first miss → reminder #1 + stamp x_studio_reminder_date
#         - second miss → final reminder + stamp x_studio_final_reminder_date
#         - third miss → archive with "Refuse did not complete assessment"
#
# Pure procedural — no nested defs, no genexp closing over outer vars.

STAGE_NEW = 1
STAGE_QUALIFICATION = 2
TPL_GENERAL_REMINDER = 'Recruitment: General Follow-up Reminder'
TPL_FINAL_REMINDER = 'Recruitment: Final Reminder Before Archive'
TPL_NON_RESPONSE = 'Recruitment: Refuse did not complete assessment'
REMINDER_INTERVAL_HOURS = 48

now = datetime.datetime.now()
cutoff = (now - datetime.timedelta(hours=REMINDER_INTERVAL_HOURS))

# ── PART 0: PROCESS QUEUED REFUSALS ────────────────────────────────────────
queued = env['hr.applicant'].search([
    ('active', '=', True),
    ('x_studio_queued_refusal_id', '!=', False),
])
for rec in queued:
    tpl_name = rec.x_studio_queued_refusal_id
    tpl = env['mail.template'].search([('name', '=', tpl_name)], limit=1)
    if not tpl.exists():
        rec.message_post(body="AUTOMATION ERROR: Queued template '%s' not found." % tpl_name)
        continue
    tpl.send_mail(rec.id, force_send=False)
    rec.write({'active': False, 'x_studio_queued_refusal_id': False, 'kanban_state': 'normal'})
    rec.message_post(body="AUTOMATION: Queued refusal '%s' sent and applicant archived." % tpl_name)


# ── PART 1: SURVEY-1 REMINDERS (Stages 1, 2) ───────────────────────────────
track1 = env['hr.applicant'].search([
    ('active', '=', True),
    ('stage_id', 'in', [STAGE_NEW, STAGE_QUALIFICATION]),
])

for rec in track1:
    # Skip if info survey is already completed
    survey = rec.job_id.x_studio_application_information if rec.job_id else False
    if survey:
        completed = env['survey.user_input'].search_count([
            ('email', '=', rec.email_from),
            ('survey_id', '=', survey.id),
            ('state', '=', 'done'),
        ])
        if completed > 0:
            continue

    # Compute last-contact date (most recent of any reminder/request date,
    # fallback to stage change). Plain for-loop, no genexp closure.
    candidate_dates = []
    if rec.x_studio_resume_request_date:
        candidate_dates.append(rec.x_studio_resume_request_date)
    if rec.x_studio_reminder_date:
        candidate_dates.append(rec.x_studio_reminder_date)
    if rec.x_studio_final_reminder_date:
        candidate_dates.append(rec.x_studio_final_reminder_date)

    if candidate_dates:
        last_date = candidate_dates[0]
        for d in candidate_dates[1:]:
            if d > last_date:
                last_date = d
    else:
        last_date = rec.date_last_stage_update

    if not last_date:
        continue
    if last_date > cutoff:
        continue
    if last_date.date() == now.date():
        continue

    # Grace period: skip if any survey activity in last 48h
    recent_activity = env['survey.user_input'].search_count([
        ('email', '=', rec.email_from),
        ('write_date', '>', cutoff.strftime('%Y-%m-%d %H:%M:%S')),
    ])
    if recent_activity > 0:
        continue

    reminder_date = rec.x_studio_reminder_date
    final_date = rec.x_studio_final_reminder_date

    if not reminder_date:
        tpl = env['mail.template'].search([('name', '=', TPL_GENERAL_REMINDER)], limit=1)
        if tpl.exists():
            tpl.send_mail(rec.id, force_send=False)
            rec.write({'x_studio_reminder_date': now})
    elif not final_date:
        tpl = env['mail.template'].search([('name', '=', TPL_FINAL_REMINDER)], limit=1)
        if tpl.exists():
            tpl.send_mail(rec.id, force_send=False)
            rec.write({
                'x_studio_final_reminder_date': now,
                'x_studio_sms_reminder_date': False,
            })
    else:
        tpl = env['mail.template'].search([('name', '=', TPL_NON_RESPONSE)], limit=1)
        if tpl.exists():
            tpl.send_mail(rec.id, force_send=False)
        rec.write({'active': False})
        rec.message_post(body="AUTOMATION: Auto-archived after unanswered Track 1 reminders.")

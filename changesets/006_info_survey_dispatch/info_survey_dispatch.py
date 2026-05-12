# TRIGGER: hr.applicant on_write
# MODEL: hr.applicant
# DESCRIPTION: When applicant enters Stage 2 (Qualification), email them
#   the Application Information Confirmation survey link with a fresh
#   per-applicant token URL.
#
#   Dedup is scoped TO THE CURRENT APPLICANT (not to email globally):
#   we only skip if a user_input for (this email, this survey) exists
#   that was created at-or-after this applicant. If the same person
#   applies for a new position, a new applicant record is created with
#   a newer create_date, prior user_inputs are filtered out, and a
#   fresh info-survey email goes out for the new application. The
#   assessment dedup (changeset 008) intentionally keeps prior
#   completions — those are once-per-candidate, this is once-per-
#   application.
#
# Pure procedural — no nested defs, no closures.

STAGE_QUALIFICATION = 2
TPL_INFO_SURVEY = 'Recruitment: Information Confirmation Survey'

# Only fire when entering Stage 2
if record.stage_id.id == STAGE_QUALIFICATION:
    if not record.email_from:
        record.message_post(body="AUTOMATION WARNING: No email on file — cannot dispatch info survey.")
    elif not record.job_id:
        record.message_post(body="AUTOMATION WARNING: No job position set — cannot dispatch info survey.")
    else:
        survey = record.job_id.x_studio_application_information
        if not survey:
            record.message_post(body=(
                "AUTOMATION WARNING: Job position '%s' has no Application "
                "Information survey configured."
            ) % (record.job_id.name or 'Unknown'))
        else:
            # Per-applicant dedup: count user_inputs with this (email,
            # survey) that were created at-or-after this applicant.
            # Anything older came from a prior application and shouldn't
            # block sending a fresh info survey for THIS application.
            already = env['survey.user_input'].search_count([
                ('email', '=', record.email_from),
                ('survey_id', '=', survey.id),
                ('create_date', '>=', record.create_date),
            ])
            if already == 0:
                user_input = env['survey.user_input'].create({
                    'survey_id': survey.id,
                    'email': record.email_from,
                    'state': 'new',
                })
                survey_url = user_input.get_start_url()
                tpl = env['mail.template'].search([('name', '=', TPL_INFO_SURVEY)], limit=1)
                if not tpl.exists():
                    record.message_post(body=(
                        "AUTOMATION ERROR: Template '%s' not found."
                    ) % TPL_INFO_SURVEY)
                else:
                    ctx = dict(env.context or {})
                    ctx['survey_link'] = survey_url
                    tpl.with_context(ctx).send_mail(record.id, force_send=False)
                    record.message_post(body=(
                        "AUTOMATION: Info Confirmation Survey sent to %s."
                    ) % record.email_from)
            else:
                record.message_post(body=(
                    "AUTOMATION: Info survey already dispatched for this application - skipping resend."
                ))

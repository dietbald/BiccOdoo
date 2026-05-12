# TRIGGER: hr.applicant on_write of stage_id
# MODEL: hr.applicant
# DESCRIPTION: When applicant enters Stage 2 (Qualification), email them
#   the Application Information Confirmation survey link. Skips silently
#   if any user_input already exists for that (email, survey) pair —
#   prevents duplicate emails on stage bounces.
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
            already = env['survey.user_input'].search_count([
                ('email', '=', record.email_from),
                ('survey_id', '=', survey.id),
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
                    "AUTOMATION: Info survey already dispatched or completed - skipping dispatch."
                ))

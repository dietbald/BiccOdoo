# TRIGGER: Manual — Action menu on hr.applicant (form + list)
# MODEL: hr.applicant
# DESCRIPTION: Seed deterministic TEST_FIXTURE_* applicants in known
#   pipeline states so the janitors / dispatchers can be exercised
#   without involving real applicants. Idempotent: existing fixture
#   rows are reset to a clean state instead of duplicated.
#
# Production guard: refuses to run if web.base.url looks like prod
# (bicc.odoo.com without a dev/ph2 marker).
#
# Pure procedural — no nested defs, no closures.

# ── Production guard ───────────────────────────────────────────────
base_url = env['ir.config_parameter'].sudo().get_param('web.base.url') or ''
lower_url = base_url.lower()
if 'bicc.odoo.com' in lower_url and 'dev' not in lower_url and 'ph2' not in lower_url and 'staging' not in lower_url:
    raise UserError(
        "Recruitment test fixtures cannot be seeded on production (%s). "
        "Run this only on bicc-dev / bicc-ph23 / other staging copies."
        % base_url
    )

# ── Locate a target job ────────────────────────────────────────────
candidate_jobs = env['hr.job'].search([
    ('active', '=', True),
    ('x_studio_application_information', '!=', False),
    ('survey_id', '!=', False),
    ('x_studio_logical_assessment', '!=', False),
    ('x_studio_emotional_assessment', '!=', False),
], limit=1)
if not candidate_jobs:
    raise UserError(
        "No active hr.job found with x_studio_application_information, "
        "survey_id, x_studio_logical_assessment AND "
        "x_studio_emotional_assessment configured. Configure those on "
        "at least one job before seeding fixtures."
    )
target_job = candidate_jobs[0]

now = datetime.datetime.now()
three_days_ago = now - datetime.timedelta(days=3)

# Fixture spec: (suffix, stage_id, backdate_to_3d_ago, seed_technical_done)
fixtures = [
    ('STAGE1_NORESUME_FRESH', 1, False, False),
    ('STAGE1_NORESUME_OLD', 1, True, False),
    ('STAGE2_NOSURVEY_FRESH', 2, False, False),
    ('STAGE2_NOSURVEY_OLD', 2, True, False),
    ('STAGE7_PARTIAL_OLD', 7, True, True),
    ('STAGE7_NODONE_OLD', 7, True, False),
]

# Fields cleared on every (re-)seed so the fixture starts in a known state
RESET_FIELDS = {
    'active': True,
    'kanban_state': 'normal',
    'x_studio_reminder_date': False,
    'x_studio_final_reminder_date': False,
    'x_studio_resume_request_date': False,
    'x_studio_assessment_reminder_date': False,
    'x_studio_assessment_final_reminder_date': False,
    'x_studio_sms_reminder_date': False,
    'x_studio_sms_new_reminder_date': False,
    'x_studio_assessment_sms_reminder_date': False,
    'x_studio_queued_refusal_id': False,
    'x_studio_assessment_pending_links': False,
}

created_ids = []
for suffix, stage_id, backdated, seed_done in fixtures:
    name = 'TEST_FIXTURE_' + suffix
    email = 'bicc-fixture-' + suffix.lower() + '@mailinator.com'

    # Clean any prior survey.user_input rows from a previous seed
    prior_inputs = env['survey.user_input'].search([('email', '=', email)])
    if prior_inputs:
        prior_inputs.unlink()

    # Idempotent applicant create/reset
    rec = env['hr.applicant'].with_context(active_test=False).search(
        [('name', '=', name)], limit=1)
    write_vals = dict(RESET_FIELDS)
    write_vals['stage_id'] = stage_id
    write_vals['job_id'] = target_job.id
    write_vals['email_from'] = email
    write_vals['partner_name'] = 'Test ' + suffix

    if rec:
        rec.write(write_vals)
    else:
        write_vals['name'] = name
        rec = env['hr.applicant'].create(write_vals)

    # Backdate date_last_stage_update for "OLD" fixtures so the 48h
    # janitor gate considers them eligible.
    if backdated:
        rec.write({'date_last_stage_update': three_days_ago})

    # Seed a "done" Technical user_input for the PARTIAL fixture so
    # Track 2 sees Logical + Emotional as missing.
    if seed_done and target_job.survey_id:
        env['survey.user_input'].create({
            'survey_id': target_job.survey_id.id,
            'email': email,
            'state': 'done',
        })

    created_ids.append(rec.id)
    rec.message_post(body=(
        "TEST FIXTURE: seeded for job '%s' (stage=%d, backdated=%s, "
        "technical_done=%s, email=%s)"
    ) % (target_job.name, stage_id, backdated, seed_done, email))

action = {
    'type': 'ir.actions.act_window',
    'name': 'TEST_FIXTURE_* applicants',
    'res_model': 'hr.applicant',
    'view_mode': 'list,form,kanban',
    'domain': [('id', 'in', created_ids)],
    'target': 'current',
}

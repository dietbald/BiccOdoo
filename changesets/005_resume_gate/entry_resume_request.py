# TRIGGER: hr.applicant on_create
# MODEL: hr.applicant
# DESCRIPTION: Entry gate. Two responsibilities on every new applicant:
#   1. Auto-detect source from partner_name/email_from keywords (Indeed,
#      LinkedIn, Facebook, Jobstreet, OnlineJobs).
#   2. Resume gate: if the job requires a resume and the applicant has
#      none, email the "Request for Resume" template — but only if the
#      applicant was NOT created by an HR user. HR users manually adding
#      an applicant typically attach the resume seconds after saving;
#      we don't want to spam the candidate before HR has had a chance.
#      External creates (website form, n8n webhook, public-portal) DO
#      get the email immediately.
#
#   Duplicate detection is intentionally NOT done here — HR handles
#   duplicates manually.
#
# Pure procedural — no nested defs, no closures.

STAGE_NEW = 1
STAGE_QUALIFICATION = 2
TPL_RESUME_REQUEST = 'Recruitment: Request for Resume (Missing Attachment)'

# Source detection: (keyword to look for in name/email, utm.source name to set)
SOURCE_PATTERNS = [
    ('via SEEK', 'Jobstreet'),
    ('via JobStreet', 'Jobstreet'),
    ('via Indeed', 'Search engine'),
    ('via LinkedIn', 'LinkedIn'),
    ('via Facebook', 'Facebook'),
    ('OnlineJobs.ph', 'OnlineJobs'),
    ('onlinejobs.ph', 'OnlineJobs'),
]


# ── 1. SOURCE AUTO-DETECTION ───────────────────────────────────────────────
name = record.partner_name or ''
email = record.email_from or ''
matched_source = None
for pattern, source_name in SOURCE_PATTERNS:
    if pattern.lower() in name.lower() or pattern.lower() in email.lower():
        matched_source = source_name
        if ' via ' in name:
            clean_name = name[:name.lower().rfind(' via ')].strip()
            if clean_name:
                record.write({'partner_name': clean_name})
        if name.lower().startswith('onlinejobs'):
            record.message_post(body=(
                "AUTOMATION: OnlineJobs.ph notification email detected. "
                "Name may need manual update."))
        break

if matched_source and not record.source_id:
    source = env['utm.source'].search([('name', '=', matched_source)], limit=1)
    if source:
        record.write({'source_id': source.id})
        record.message_post(body="AUTOMATION: Source auto-detected as '%s'." % matched_source)


# ── 2. RESUME GATE ──────────────────────────────────────────────────────────
needs_resume = bool(record.job_id and record.job_id.x_studio_resume_required) and record.attachment_number == 0

if needs_resume:
    # Skip the email when the creator is an HR user — they'll attach the
    # resume themselves seconds after saving. Auto-applicants (website
    # form, n8n webhook, etc.) have a non-HR create_uid (public user, API
    # user, OdooBot) and DO get the email immediately.
    created_by_hr = bool(
        record.create_uid and
        record.create_uid.has_group('hr_recruitment.group_hr_recruitment_user')
    )

    if created_by_hr:
        record.message_post(body=(
            "AUTOMATION: Created by HR user (%s). Resume-request email "
            "skipped — please attach the resume manually."
        ) % (record.create_uid.name or 'unknown'))
    elif record.email_from:
        tpl = env['mail.template'].search([('name', '=', TPL_RESUME_REQUEST)], limit=1)
        if tpl.exists():
            tpl.send_mail(record.id, force_send=False)
            record.write({'x_studio_resume_request_date': datetime.datetime.now()})
            record.message_post(body="AUTOMATION: Resume required but missing. Request sent.")
        else:
            record.message_post(body=(
                "AUTOMATION ERROR: Template '%s' not found."
            ) % TPL_RESUME_REQUEST)
    else:
        record.message_post(body="AUTOMATION: Resume required but missing. No email to send request.")
else:
    record.write({'stage_id': STAGE_QUALIFICATION})
    record.message_post(body="AUTOMATION: Qualifications met. Moving to Qualification stage.")

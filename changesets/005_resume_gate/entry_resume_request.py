# TRIGGER: hr.applicant on_create
# MODEL: hr.applicant
# DESCRIPTION: Entry gate. Two responsibilities on every new applicant:
#   1. Auto-detect source from partner_name/email_from keywords (Indeed,
#      LinkedIn, Facebook, Jobstreet, OnlineJobs).
#   2. Resume gate: email the "Request for Resume" template ONLY when
#      the applicant came through Jobstreet/SEEK or the website careers
#      form, AND has no resume attached, AND the job requires a resume.
#      All other channels (Indeed, LinkedIn, OnlineJobs, HR manual
#      creates, unknown) are excluded — HR handles those manually.
#      Facebook traffic goes through the BICC website first and submits
#      via the careers form, so it's covered by the "Website" branch.
#
#   This server action NEVER moves applicants to Stage 2. n8n owns the
#   Stage 1 → Stage 2 transition.
#
#   Duplicate detection is intentionally NOT done here — HR handles
#   duplicates manually.
#
# Pure procedural — no nested defs, no closures.

TPL_RESUME_REQUEST = 'Recruitment: Request for Resume (Missing Attachment)'

# Source detection: (keyword to look for in name/email, utm.source name to set)
SOURCE_PATTERNS = [
    ('via SEEK', 'Jobstreet'),
    ('via JobStreet', 'Jobstreet'),
    ('via Indeed', 'Search engine'),
    ('via LinkedIn', 'LinkedIn'),
    ('OnlineJobs.ph', 'OnlineJobs'),
    ('onlinejobs.ph', 'OnlineJobs'),
]

# Detected-source names that should trigger the resume-request email.
# Everything else is a manual / unknown channel and HR handles it.
# (Facebook is not listed because Facebook applicants apply via the BICC
# website and are covered by the public-user "Website" detection below.)
EMAIL_TRIGGER_SOURCES = ('Jobstreet', 'Website')


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
    # Detect "website careers form" submissions: create_uid is the public
    # user (Odoo's standard for portal-form submissions). The website
    # module typically leaves source_id empty, so we don't expect a
    # matched_source for these.
    public_user = env.ref('base.public_user', raise_if_not_found=False)
    is_website_form = bool(
        public_user and
        record.create_uid and
        record.create_uid.id == public_user.id
    )

    fires_email = (matched_source in EMAIL_TRIGGER_SOURCES) or is_website_form

    if fires_email:
        if record.email_from:
            tpl = env['mail.template'].search([('name', '=', TPL_RESUME_REQUEST)], limit=1)
            if tpl.exists():
                tpl.send_mail(record.id, force_send=False)
                record.write({'x_studio_resume_request_date': datetime.datetime.now()})
                channel = matched_source or 'website form'
                record.message_post(body=(
                    "AUTOMATION: Resume required but missing. Request sent (channel: %s)."
                ) % channel)
            else:
                record.message_post(body=(
                    "AUTOMATION ERROR: Template '%s' not found."
                ) % TPL_RESUME_REQUEST)
        else:
            record.message_post(body=(
                "AUTOMATION: Resume required but missing. No email to send request."
            ))
    else:
        # Channel is excluded from the auto-trigger (Indeed, LinkedIn,
        # OnlineJobs, HR manual create, or unknown). HR will follow up
        # manually.
        record.message_post(body=(
            "AUTOMATION: Resume missing. Auto-request email skipped - "
            "channel '%s' is not in the auto-trigger list "
            "(Jobstreet/SEEK, Website). HR to follow up manually."
        ) % (matched_source or 'manual / unknown'))

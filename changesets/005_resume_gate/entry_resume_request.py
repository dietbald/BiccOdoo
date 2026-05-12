# TRIGGER: hr.applicant on_create
# MODEL: hr.applicant
# DESCRIPTION: Entry gate. Three responsibilities on every new applicant:
#   1. Auto-detect source from partner_name/email_from keywords
#   2. Duplicate check within 30-day window for same (email, job) — if a
#      duplicate exists, archive the new record and transfer attachments
#      to the original if needed.
#   3. Resume gate: if job requires a resume and applicant has none,
#      email the "Request for Resume" template and stamp
#      x_studio_resume_request_date. Otherwise advance to Stage 2.
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

# ── 0. SOURCE AUTO-DETECTION ───────────────────────────────────────────────
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


# ── 1. DUPLICATE CHECK + 2. RESUME GATE  ────────────────────────────────────
# We inline the resume-gate logic in two places (once for "no email"
# branch, once for "no duplicate" branch) to avoid a nested def.

is_duplicate = False
if record.email_from:
    cutoff = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
    duplicate = env['hr.applicant'].search([
        ('email_from', '=', record.email_from),
        ('job_id', '=', record.job_id.id if record.job_id else False),
        ('id', '!=', record.id),
        ('create_date', '>', cutoff),
    ], limit=1)
    if duplicate:
        is_duplicate = True
        if (duplicate.stage_id.id == STAGE_NEW
                and duplicate.attachment_number == 0
                and record.attachment_number > 0):
            attachments = env['ir.attachment'].search([
                ('res_model', '=', 'hr.applicant'),
                ('res_id', '=', record.id),
            ])
            if attachments:
                attachments.write({'res_id': duplicate.id})
                duplicate.message_post(body=(
                    "AUTOMATION: Transferred %d attachment(s) from duplicate "
                    "Applicant #%d."
                ) % (len(attachments), record.id))
        record.message_post(body=(
            "AUTO-ARCHIVE: Duplicate of Applicant #%d (same email + job within 30 days)."
        ) % duplicate.id)
        record.write({'active': False})

if not is_duplicate:
    # Resume gate
    needs_resume = bool(record.job_id and record.job_id.x_studio_resume_required) and record.attachment_number == 0
    if needs_resume:
        if record.email_from:
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

# TRIGGER: Manual button on hr.applicant (Action menu) OR menu item
#          (Recruitment → Reporting → SMS Follow-up Queue).
# MODEL: hr.applicant
# DESCRIPTION: Email the HR Recruitment Manager group a single digest of every
#   applicant who needs an SMS follow-up right now, grouped by job position.
#   For each job there is ONE table with three columns (Applicant name with
#   link, mobile number, ready-to-send SMS text).
#
#   Queue gate is now PURELY stage age + SMS-not-yet-sent — the queue does
#   NOT require an email reminder to have fired first. Whether HR sent the
#   email reminders or not, applicants overdue in their current stage show
#   up in the SMS queue so HR can SMS them directly.
#
# Pattern note: Odoo SaaS safe_eval forbids closures (LOAD_CLOSURE / MAKE_CELL)
# inside lambdas / comprehensions / nested defs. Everything below is plain
# procedural — no nested def, no genexp closing over outer-scope variables.

STAGE_NEW = 1
STAGE_QUALIFICATION = 2
STAGE_ASSESSMENT_SENT = 7

# How long an applicant must have been in the current stage before they show
# up in the SMS follow-up queue. Tune this if HR wants to chase candidates
# sooner or later.
OVERDUE_DAYS = 3

now = datetime.datetime.now()
threshold = (now - datetime.timedelta(days=OVERDUE_DAYS)).strftime('%Y-%m-%d %H:%M:%S')
base_url = env['ir.config_parameter'].sudo().get_param('web.base.url', '')
company_name = env.company.name if env.company else 'BICC'

# Field-availability flags. We only depend on the per-queue SMS-dedup fields
# now (the email-reminder-date fields are no longer in the gate).
fld = env['ir.model.fields'].sudo()
has_sms_reminder_date = bool(fld.search(
    [('model', '=', 'hr.applicant'), ('name', '=', 'x_studio_sms_reminder_date')], limit=1))
has_sms_new_reminder_date = bool(fld.search(
    [('model', '=', 'hr.applicant'), ('name', '=', 'x_studio_sms_new_reminder_date')], limit=1))
has_assessment_sms_date = bool(fld.search(
    [('model', '=', 'hr.applicant'), ('name', '=', 'x_studio_assessment_sms_reminder_date')], limit=1))
has_short_name = bool(fld.search(
    [('model', '=', 'res.company'), ('name', '=', 'x_studio_short_name')], limit=1))


# Build flat list of (applicant, sms_message). The SMS wording is built
# inline per-candidate so the kind is captured in the string itself.
entries = []
n_qual = 0
n_resume = 0
n_asses = 0


# ── Queue 1: Qualification (Stage 2) ───────────────────────────────────────
if has_sms_reminder_date:
    qual_candidates = env['hr.applicant'].search([
        ('active', '=', True),
        ('stage_id', '=', STAGE_QUALIFICATION),
        ('date_last_stage_update', '<', threshold),
        ('x_studio_sms_reminder_date', '=', False),
    ])
    n_qual = len(qual_candidates)
    for r in qual_candidates:
        co_short = False
        if r.company_id and has_short_name:
            co_short = r.company_id.x_studio_short_name
        co = co_short or (r.company_id.name if r.company_id else 'BICC')
        first_name = (r.partner_name or 'there').split(' ')[0]
        job = r.job_id.name if r.job_id else 'open'
        message = (
            "Hi %s, this is %s HR. We sent you the Applicant Information form "
            "for the %s role a few days back. Could you fill it out so we can "
            "keep things moving? If you didn't get our email, let us know."
        ) % (first_name, co, job)
        entries.append((r, message))


# ── Queue 2: Resume Missing (Stage 1, no attachment) ───────────────────────
if has_sms_new_reminder_date:
    resume_pool = env['hr.applicant'].search([
        ('active', '=', True),
        ('stage_id', '=', STAGE_NEW),
        ('date_last_stage_update', '<', threshold),
        ('x_studio_sms_new_reminder_date', '=', False),
    ])
    resume_ids = []
    for r in resume_pool:
        if r.attachment_number == 0:
            resume_ids.append(r.id)
    resume_candidates = env['hr.applicant'].browse(resume_ids)
    n_resume = len(resume_candidates)
    for r in resume_candidates:
        co_short = False
        if r.company_id and has_short_name:
            co_short = r.company_id.x_studio_short_name
        co = co_short or (r.company_id.name if r.company_id else 'BICC')
        first_name = (r.partner_name or 'there').split(' ')[0]
        job = r.job_id.name if r.job_id else 'open'
        message = (
            "Hi %s, %s HR here. We got your application for the %s role but "
            "didn't see a resume attached. Could you reply to our email with it? "
            "If you never got our email, let us know."
        ) % (first_name, co, job)
        entries.append((r, message))


# ── Queue 3: Assessment (Stage 7) ──────────────────────────────────────────
if has_assessment_sms_date:
    asses_candidates = env['hr.applicant'].search([
        ('active', '=', True),
        ('stage_id', '=', STAGE_ASSESSMENT_SENT),
        ('date_last_stage_update', '<', threshold),
        ('x_studio_assessment_sms_reminder_date', '=', False),
    ])
    n_asses = len(asses_candidates)
    for r in asses_candidates:
        co_short = False
        if r.company_id and has_short_name:
            co_short = r.company_id.x_studio_short_name
        co = co_short or (r.company_id.name if r.company_id else 'BICC')
        first_name = (r.partner_name or 'there').split(' ')[0]
        job = r.job_id.name if r.job_id else 'open'
        message = (
            "Hi %s, %s HR here. Have you had a chance to do the assessment we "
            "emailed you for the %s role? Please send it back when you can. "
            "If you can't find our email, let us know."
        ) % (first_name, co, job)
        entries.append((r, message))


# ── Group by job, then render ──────────────────────────────────────────────
groups = {}
for applicant, message in entries:
    job_label = applicant.job_id.name if applicant.job_id else '(No job position)'
    if job_label not in groups:
        groups[job_label] = []
    groups[job_label].append((applicant, message))

job_labels = list(groups.keys())
job_labels.sort()

sections_html = ""
total_count = len(entries)

for job_label in job_labels:
    job_entries = groups[job_label]
    rows_html = ""
    for applicant, message in job_entries:
        name = applicant.partner_name or 'Unknown'
        link = "%s/odoo/recruitment-applications/%s" % (base_url, applicant.id)
        phone = applicant.partner_phone or '(no phone on file)'
        rows_html += (
            "<tr>"
            "<td><a href='%s'><b>%s</b></a></td>"
            "<td>%s</td>"
            "<td style='font-family:monospace;font-size:0.88em;white-space:pre-wrap;'>%s</td>"
            "</tr>"
        ) % (link, name, phone, message)

    sections_html += (
        "<h3 style='margin-top:24px;color:#101820;'>%s (%d candidate(s))</h3>"
        "<table border='1' cellpadding='8' cellspacing='0' "
        "style='border-collapse:collapse;width:100%%;'>"
        "<thead style='background:#f2f2f2;'><tr>"
        "<th align='left'>Applicant</th>"
        "<th align='left'>Mobile</th>"
        "<th align='left'>SMS to send</th>"
        "</tr></thead>"
        "<tbody>%s</tbody>"
        "</table>"
    ) % (job_label, len(job_entries), rows_html)


# ── Resolve HR recipients (fallback to triggering user if HR group empty) ──
hr_group = env.ref('hr_recruitment.group_hr_recruitment_manager', raise_if_not_found=False)
notify_partners = env['res.partner']
if hr_group:
    notify_partners = hr_group.user_ids.filtered('active').mapped('partner_id')

recipient_source = 'HR Recruitment Manager group'
if not notify_partners and env.user and env.user.partner_id:
    notify_partners = env.user.partner_id
    recipient_source = 'fallback: triggering user (HR group resolved to 0 partners)'

recipient_names = []
for p in notify_partners:
    recipient_names.append(p.name or 'Unknown')


# ── Debug block (always appended, collapsed by default) ────────────────────
debug_html = (
    "<hr style='margin-top:32px;border:none;border-top:1px solid #ddd;'/>"
    "<details><summary style='cursor:pointer;color:#666;font-size:0.85em;'>"
    "Debug info (click to expand)</summary>"
    "<pre style='font-family:monospace;font-size:0.82em;color:#444;"
    "background:#f9f9f9;padding:12px;border:1px solid #eee;'>"
    "Triggered at: %s\n"
    "Server time UTC: %s\n"
    "Triggering user: %s (uid=%d)\n"
    "Company: %s\n"
    "Overdue threshold: %d day(s) (applicants stuck since before %s)\n"
    "\n"
    "Field-existence flags (queue gate = SMS dedup field exists):\n"
    "  res.company.x_studio_short_name                       = %s\n"
    "  hr.applicant.x_studio_sms_reminder_date               = %s  (Qualification gate)\n"
    "  hr.applicant.x_studio_sms_new_reminder_date           = %s  (Resume Missing gate)\n"
    "  hr.applicant.x_studio_assessment_sms_reminder_date    = %s  (Assessment gate)\n"
    "\n"
    "Queue counts:\n"
    "  Qualification (Stage 2, overdue)              : %d\n"
    "  Resume missing (Stage 1, overdue, no resume)  : %d\n"
    "  Assessment (Stage 7, overdue)                 : %d\n"
    "  TOTAL                                          : %d\n"
    "\n"
    "Recipient resolution:\n"
    "  Source: %s\n"
    "  Count : %d\n"
    "  Names : %s\n"
    "</pre></details>"
) % (
    now.isoformat(timespec='seconds'),
    datetime.datetime.utcnow().isoformat(timespec='seconds') + 'Z',
    env.user.name if env.user else '(no user)',
    env.uid or 0,
    company_name,
    OVERDUE_DAYS,
    threshold,
    has_short_name,
    has_sms_reminder_date,
    has_sms_new_reminder_date,
    has_assessment_sms_date,
    n_qual,
    n_resume,
    n_asses,
    total_count,
    recipient_source,
    len(notify_partners),
    ', '.join(recipient_names) if recipient_names else '(none)',
)


# ── Email body assembly ────────────────────────────────────────────────────
if total_count > 0:
    subject = "%s SMS Queue: %d candidate(s) need a follow-up SMS" % (company_name, total_count)
    header = (
        "<h2 style='color:#101820;'>%s SMS Queue (manual request)</h2>"
        "<p>Below is one section per job position with the candidates who need "
        "an SMS follow-up right now. Copy the <b>SMS to send</b> column into "
        "your phone, text it to the matching number, then mark the SMS "
        "reminder date on the applicant record so the queue clears.</p>"
    ) % company_name
else:
    subject = "%s SMS Queue: nothing to send right now" % company_name
    header = (
        "<h2 style='color:#101820;'>%s SMS Queue (manual request)</h2>"
        "<p style='color:#666;'><i>No applicants currently match the SMS "
        "follow-up criteria. See the debug section below for the field "
        "flags and queue counts.</i></p>"
    ) % company_name

body_html = header + sections_html + debug_html


# ── Always create + send mail.mail (auto_delete=False so it stays visible) ─
recipient_cmds = []
for pid in notify_partners.ids:
    recipient_cmds.append((4, pid))

mail = env['mail.mail'].sudo().create({
    'subject': subject,
    'body_html': body_html,
    'recipient_ids': recipient_cmds,
    'auto_delete': False,
})
mail.send()


# ── If triggered from a specific applicant (gear menu), post to its chatter ─
if record and record._name == 'hr.applicant':
    record.message_post(body=(
        "MANUAL ACTION: SMS Queue Digest fired. "
        "Counts → qual=%d, resume=%d, assessment=%d, total=%d. "
        "Recipients=%d (%s). mail.mail id=%d."
    ) % (n_qual, n_resume, n_asses, total_count, len(notify_partners), recipient_source, mail.id))


log("SMS queue digest: total=%d (qual=%d resume=%d assess=%d) threshold=%dd recipients=%d mail.id=%d" % (
    total_count, n_qual, n_resume, n_asses, OVERDUE_DAYS, len(notify_partners), mail.id
))

# TRIGGER: Weekly Scheduled Action (Monday 8:00 AM PHT)
# MODEL: hr.applicant
# DESCRIPTION: Weekly KPI digest — Star Leakage, Overall Pass Rate,
#   Assessment Drop-off (Jeepney Test), and Source ROI.
#   Pure procedural — no nested defs, no lambdas, no comps capturing
#   outer variables.

STAGE_ASSESSMENT_SENT = 7
STAGE_PASSED_ASSESSMENT = 10

now = datetime.datetime.now()
last_week = now - datetime.timedelta(days=7)
last_week_str = last_week.strftime('%Y-%m-%d %H:%M:%S')
company_name = env.company.name or 'Our Company'
base_url = env['ir.config_parameter'].sudo().get_param('web.base.url', '')

hr_group = env.ref('hr_recruitment.group_hr_recruitment_manager', raise_if_not_found=False)
notify_partners = env['res.partner']
if hr_group:
    notify_partners = hr_group.user_ids.filtered('active').mapped('partner_id')

# 1. STAR LEAKAGE — star candidates not contacted within 24h
stars = env['hr.applicant'].search([
    ('priority', '=', '3'),
    ('create_date', '>', last_week_str),
])
leaked = []
for s in stars:
    if not s.date_open:
        leaked.append(s)
    else:
        response_hours = (s.date_open - s.create_date).total_seconds() / 3600
        if response_hours > 24:
            leaked.append(s)

# 2. OVERALL PASS RATE
total_new = env['hr.applicant'].with_context(active_test=False).search_count([
    ('create_date', '>', last_week_str),
])
total_passed = env['hr.applicant'].search_count([
    ('stage_id', '=', STAGE_PASSED_ASSESSMENT),
    ('create_date', '>', last_week_str),
])
pass_rate = (total_passed / total_new * 100) if total_new > 0 else 0

# 3. ASSESSMENT DROP-OFF
reached_assessment = env['hr.applicant'].with_context(active_test=False).search([
    ('stage_id', 'in', [STAGE_ASSESSMENT_SENT, STAGE_PASSED_ASSESSMENT]),
    ('create_date', '>', last_week_str),
])
completed_assessment = env['hr.applicant'].search([
    ('stage_id', '=', STAGE_PASSED_ASSESSMENT),
    ('create_date', '>', last_week_str),
])
dropoff_count = len(reached_assessment) - len(completed_assessment)
dropoff_rate = (dropoff_count / len(reached_assessment) * 100) if reached_assessment else 0

# 4. SOURCE ROI
all_new = env['hr.applicant'].with_context(active_test=False).search([
    ('create_date', '>', last_week_str),
])
source_stats = {}
for a in all_new:
    src = a.source_id.name if a.source_id else 'Unknown'
    if src not in source_stats:
        source_stats[src] = {'total': 0, 'passed': 0}
    source_stats[src]['total'] += 1
    if a.stage_id.id == STAGE_PASSED_ASSESSMENT:
        source_stats[src]['passed'] += 1

# Sort source_stats by total desc — using tuple sort, no lambda
sortable_sources = []
for src, data in source_stats.items():
    sortable_sources.append((data['total'], data['passed'], src))
sortable_sources.sort(reverse=True)

source_rows = ""
for total, passed, src in sortable_sources:
    src_pass_rate = (passed / total * 100) if total > 0 else 0
    source_rows += (
        "<tr><td>%s</td><td>%d</td><td>%d</td><td>%.1f%%</td></tr>"
    ) % (src, total, passed, src_pass_rate)

# Build email body
body_html = "<h2>%s Recruitment Weekly Digest</h2>" % company_name
body_html += "<p>Period: <b>%s</b> to <b>%s</b></p>" % (
    last_week.strftime('%B %d, %Y'), now.strftime('%B %d, %Y'))

body_html += "<h3>1. Star Leakage</h3>"
body_html += "<p><b>Star candidates found:</b> %d</p>" % len(stars)
body_html += "<p><b>Star leakage (not contacted in 24h):</b> %d</p>" % len(leaked)
if leaked:
    body_html += "<ul>"
    for s in leaked:
        link = "%s/odoo/recruitment-applications/%s" % (base_url, s.id)
        body_html += "<li><a href='%s'>%s</a> - %s</li>" % (
            link, s.partner_name or 'Unknown', s.job_id.name or '')
    body_html += "</ul>"

body_html += "<h3>2. Overall Pipeline</h3>"
body_html += "<p><b>New applicants:</b> %d | <b>Passed assessment:</b> %d | <b>Pass rate:</b> %.1f%%</p>" % (
    total_new, total_passed, pass_rate)

body_html += "<h3>3. Assessment Drop-off (Jeepney Test)</h3>"
body_html += "<p><b>Reached assessment stage:</b> %d | <b>Dropped off:</b> %d (%.1f%%)</p>" % (
    len(reached_assessment), dropoff_count, dropoff_rate)
if dropoff_rate > 40:
    body_html += "<p style='color:red;'><b>WARNING:</b> High drop-off rate — assessments may be too long for mobile.</p>"

body_html += "<h3>4. Source ROI</h3>"
if source_rows:
    body_html += "<table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse'>"
    body_html += "<thead><tr><th>Source</th><th>Applicants</th><th>Passed</th><th>Pass Rate</th></tr></thead>"
    body_html += "<tbody>" + source_rows + "</tbody></table>"
else:
    body_html += "<p>No source data available this week.</p>"

# Send
if notify_partners:
    recipient_cmds = []
    for pid in notify_partners.ids:
        recipient_cmds.append((4, pid))
    env['mail.mail'].sudo().create({
        'subject': "%s Recruitment Weekly Digest - %s" % (company_name, now.strftime('%b %d')),
        'body_html': body_html,
        'recipient_ids': recipient_cmds,
        'auto_delete': True,
    }).send()
    log("Weekly KPI digest: %d recipient(s)" % len(notify_partners))
else:
    log("Weekly KPI digest: no recipients — skipped")

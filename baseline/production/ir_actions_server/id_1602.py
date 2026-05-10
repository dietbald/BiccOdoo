# Server Action – model: hr.applicant – "Execute Python Code"
# context will carry start/stop datetimes in UTC from your wizard

start_dt = context['start_dt_utc']   # datetime (UTC)
end_dt   = context['end_dt_utc']

job_title = record.job_id.name or "Interview"
company   = record.company_id.name if record.company_id else env.company.name
location  = "Block 21 Lot 4 Ledesco Ave, Village, Iloilo City, 5000 Iloilo, Philippines"

# ------------------------------------------------------------------ attendees
attendees = []

# applicant
if record.email_from:
    attendees.append((0, 0, {
        'email': record.email_from,
        'role' : 'REQ-PARTICIPANT',
    }))

# interviewers (users) -> partners -> email
for user in record.interviewer_ids:
    if user.email:
        attendees.append((0, 0, {
            'partner_id': user.partner_id.id,
            'email'     : user.email,
            'role'      : 'CHAIR',       # or 'OPT-PARTICIPANT' if you prefer
        }))

# ------------------------------------------------------------------ event
title = f"{job_title} F2F Scheduled Interview – {record.partner_name}"

description = f"""
Dear {record.partner_name},<br/><br/>
We are pleased to confirm your interview for the position of <b>{job_title}</b> at {company}.<br/><br/>
<b>Date & Time:</b> {fields.Datetime.context_timestamp(record, start_dt).strftime('%A, %B %d, %Y ▸ %I:%M %p')}<br/>
<b>Location:</b> {location}<br/><br/>
Please arrive at least 10 minutes early and bring the requested documents.<br/><br/>
Warm regards,<br/>Recruitment Team
"""

env['calendar.event'].create({
    'name'        : title,
    'start'       : start_dt,
    'stop'        : end_dt,
    'allday'      : False,
    'location'    : location,
    'description' : description,
    'attendee_ids': attendees,
    'user_id'     : env.user.id,           # owner/organiser
})

record.message_post(
    body=f"Interview scheduled on {fields.Datetime.context_timestamp(record, start_dt).strftime('%B %d %I:%M %p')}",
    subtype_xmlid="mail.mt_note",
)

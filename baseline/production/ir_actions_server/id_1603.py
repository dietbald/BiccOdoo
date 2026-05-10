# ---------- 1. dynamic bits -------------------------------------------------
job_title   = record.job_id.name or "Interview"
candidate   = record.partner_name
company     = record.company_id.name if record.company_id else env.company.name
location    = "Block 21 Lot 4 Ledesco Ave, Village, Iloilo City, 5000 Iloilo, Philippines"



# ---------- 2. title & description -----------------------------------------
title = f"{job_title} F2F Scheduled Interview – {candidate}"
# ------------------------------------------------------------------
# 2. description – new wording & HTML
# ------------------------------------------------------------------
description = f"""
<p>Dear {candidate},</p>

<p>We are pleased to confirm your interview for the position of
<strong>{job_title}</strong> at {company}. The details of your interview are
as follows:</p>

<p><strong>Date and Time:</strong> (see calendar invitation)<br/>
<strong>Location:</strong> {location} (<a href="https://maps.app.goo.gl/zQ1XBoLzTYrJQDDCA">View&nbsp;Map</a>)</p>

<p>Please arrive at the office reception where you will be greeted and
directed to the interview room. We recommend arriving at least 10 minutes
early to allow for any unforeseen delays.</p>

<p>Could you please bring the following documents:</p>
<ul>
  <li>Resume</li>
  <li>Valid&nbsp;ID</li>
  <li>Photocopy of Diplomas and Certificates</li>
  <li>Photocopy of Transcript of Records</li>
  <li>Professional License (if any)</li>
</ul>

<p>If you have any special requirements or questions ahead of your
interview, please let us know.</p>

<p>We look forward to meeting you and discussing how you can contribute to
our team at {company}.</p>

<p>Warm regards,<br/>
Recruitment&nbsp;Team<br/>
Phone: +63 (0)&nbsp;917&nbsp;324&nbsp;8890<br/>
{company} · {location}</p>
"""

# ---------- 3. attendees: candidate + interviewer users --------------------
partner_ids = []
if record.partner_id:
    partner_ids.append(record.partner_id.id)          # candidate
for user in record.interviewer_ids:
    if user.partner_id:
        partner_ids.append(user.partner_id.id)        # interviewers
        
        
# ---------- 4. open calendar.event form as a modal --------------------------
# user will pick the date & time, then hit Save → Outlook sync fires
action = {
    'type'      : 'ir.actions.act_window',
    'res_model' : 'calendar.event',
    'view_mode' : 'form',
    'target'    : 'new',
    'context'   : {
        'default_name'        : title,
        'default_location'    : location,
        'default_description' : description,
        # pre-set attendees
        'default_partner_ids' : [(6, 0, partner_ids)],
        # link back to applicant (optional but handy)
        'default_applicant_id': record.id,
    },
}

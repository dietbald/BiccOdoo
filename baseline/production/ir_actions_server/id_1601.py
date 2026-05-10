# ------------------------------------------------------------------
# 1. Dynamic fields
# ------------------------------------------------------------------
applicant_name = record.partner_name or "Applicant"
job_title      = record.job_id.name  or "Position"
start_date     = record.x_studio_proposed_start_date
start_str      = start_date.strftime('%A, %B %d, %Y') if start_date else "TBD"
company_name = record.company_id.name if record.company_id else env.company.name


docs = [
    "Clear copies of your PAG-IBIG ID, UMID ID, PHILHEALTH ID, TIN ID, and DRIVER’S LICENSE",
    "Transcript of Records (TOR) and Diploma",
    "NBI Clearance",
    "Certificate of Employment",
    "Certificates of Training",
    "BPI Bank Details (Account Number, Account Name, Bank Name & Branch)",
]
docs_html = "".join(f"<li>{d}</li>" for d in docs)

# ------------------------------------------------------------------
# 2. Build the HTML message
# ------------------------------------------------------------------
html_body = f"""
<p> Welcome to {company_name} - Your Job Offer </p>
<br/><br/><br/>
<p>Dear <strong>{applicant_name}</strong>,</p>
<br/>
<p>We are thrilled to extend to you an offer for the position of
<strong>{job_title}</strong> at {company_name}. Please find attached the offer
letter with all the details of your employment.<br/><br/>
Kindly review, sign, and return the document <strong>within 48 hours</strong>
if you decide to accept this offer.</p>
<br/><br/>
<p><strong>First-day details:</strong><br/>
<b>Start date:</b> {start_str}<br/>
<b>Time:</b> 9 : 00 AM at the office<br/>
<b>Required documents:</b></p>

<ul>{docs_html}</ul>
<br/>
<p>You will also sign your employment agreement on your first day.</p>
<br/>
<p>We are excited about the possibility of you joining our team and
contributing to our success!</p>
<br/>
<p>Warm regards,<br/>
T.J.
<br/>{company_name}
</p>
"""

# ------------------------------------------------------------------
# 3. Post as a normal note that renders HTML
# ------------------------------------------------------------------
record.message_post(
    body=html_body.strip(),
    body_is_html=True,            # <-- THE crucial flag
    message_type="comment",       # ordinary note (green sticky-note icon)
    subtype_xmlid="mail.mt_note",
    author_id=env.user.partner_id.id,
)

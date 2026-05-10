
# Loop through selected applicants
for applicant in records:

    if not applicant.email_from:
        applicant.message_post(body="Skipping survey send: applicant has no email.")
        continue

    if not applicant.job_id:
        applicant.message_post(body="Skipping survey send: applicant has no Job Position.")
        continue

    survey = applicant.job_id.x_studio_application_information
    if not survey:
        applicant.message_post(
            body="Skipping survey send: job '%s' has no Application Information survey assigned (x_studio_application_information). Configure the survey on the job position to enable this."
            % applicant.job_id.name
        )
        continue

    try:
        survey.check_validity()
    except Exception as e:
        applicant.message_post(
            body="Skipping survey send: survey '%s' for job '%s' is invalid: %s"
            % (survey.title, applicant.job_id.name, str(e))
        )
        continue

    survey_id = survey.id

    user_input = env["survey.user_input"].search([
        ("survey_id", "=", survey_id),
        ("applicant_id", "=", applicant.id),
    ], order="create_date desc", limit=1)

    if user_input:
        continue

    user_input = env["survey.user_input"].create({
        "survey_id": survey_id,
        "partner_id": applicant.partner_id.id if applicant.partner_id else False,
        "email": applicant.email_from,
        "applicant_id": applicant.id,
        "state": "new",
    })

    email_template = env['mail.template'].browse(77)

    custom_ctx = {
        'survey_link': user_input.get_start_url(),
    }
    email_template = email_template.with_context(custom_ctx)

    if email_template:
        mail_id = email_template.send_mail(applicant.id, force_send=False)
        applicant.message_post(body="Request Applicant Information sent")
    else:
        applicant.message_post(body="Request Applicant Information NOT sent")

    applicant.write({'kanban_state': 'blocked'})

deadline_days = 7


template = env.ref("mail_template_recruitment.mail_template_applicant_multi_test", raise_if_not_found=False)

for record in records:
  

    if record.state != 'done':
        continue

    applicant = record.applicant_id
    if not applicant:
        applicant.message_post(body='No assessments sent. No applicant on this application.')
        continue

    job = applicant.job_id
    # If job missing, just log
    if not job:
        applicant.message_post(body='No assessments sent. No job position on this application.')
        continue   
    
    if not job.x_studio_application_information:
        applicant.message_post(body='No assessments sent. No x_studio_application_information on this application.')
        continue
    
    # Only survey 62 completion
    if not record.survey_id or record.survey_id.id != job.x_studio_application_information.id:
        applicant.message_post(
            body=(
                "No assessments sent. Different survey completed on this application."
                f"<br/><br/><b>record.survey_id:</b> {record.survey_id}"
                f"<br/><b>record.survey_id.id:</b> {record.survey_id.id if record.survey_id else 'None'}"
                f"<br/><b>job.x_studio_application_information:</b> {job.x_studio_application_information}"
            )
        )
        continue
    
    applicant.message_post(body='Applicant information form completed.')



    technical_survey = job.survey_id
    logical_survey = job.x_studio_logical_assessment
    emotional_survey = job.x_studio_emotional_assessment

    missing = []
    if not technical_survey:
        missing.append("technical")
    if not logical_survey:
        missing.append("logical")
    if not emotional_survey:
        missing.append("emotional")

    if missing:
        applicant.message_post(body="No assessments sent. No surveys for this job position. Missing: %s" % (", ".join(missing)))
        continue

    # Ensure partner exists (NO direct assignment, use write)
    if not applicant.partner_id:
        name = applicant.partner_name or applicant.name
        if not name:
            applicant.message_post("Please provide an applicant name.")
        partner = env["res.partner"].sudo().create({
            "is_company": False,
            "name": name,
            "email": applicant.email_from,
            "phone": applicant.partner_phone,
            "mobile": applicant.partner_mobile,
        })
        applicant.write({"partner_id": partner.id})

    # Template required
    if not template:
        applicant.message_post(body="Assessments not sent. Email template not found: mail_template_recruitment.mail_template_applicant_multi_test")
        continue

    # Validate surveys
    try:
        technical_survey.check_validity()
        logical_survey.check_validity()
        emotional_survey.check_validity()
    except:
        applicant.message_post(body="Assessments not sent. One or more surveys are not valid or not configured correctly.")
        continue

    # Related applications (same partner else same email)
    related_app_ids = [applicant.id]
    if applicant.partner_id:
        rel = env["hr.applicant"].search([("partner_id", "=", applicant.partner_id.id)])
        for a in rel:
            if a.id not in related_app_ids:
                related_app_ids.append(a.id)
    elif applicant.email_from:
        rel = env["hr.applicant"].search([("email_from", "=", applicant.email_from)])
        for a in rel:
            if a.id not in related_app_ids:
                related_app_ids.append(a.id)

    # If any assessment already done in this or related applications, do not send
    done_any = env["survey.user_input"].search([
        ("survey_id", "in", [technical_survey.id, logical_survey.id, emotional_survey.id]),
        ("applicant_id", "in", related_app_ids),
        ("state", "=", "done"),
    ], limit=1)

    if done_any:
        # Move stage to "Assessment Sent" and block
        stage = env["hr.recruitment.stage"].search([
            ("name", "=", "Assessment Sent"),
            ("job_ids", "in", [job.id]),
        ], limit=1)
        if not stage:
            stage = env["hr.recruitment.stage"].search([("name", "=", "Assessment Sent")], limit=1)
    
        vals = {"kanban_state": "blocked"}
        if stage:
            vals["stage_id"] = stage.id
        applicant.write(vals)
    
        applicant.message_post(
            body="Assessments not sent because at least one assessment was already completed in this or a related application. "
                 "Applicant moved to Assessment Sent and marked as blocked."
        )
        continue        

    # If pending links already exist for this applicant, do not resend
    pending_any = env["survey.user_input"].search([
        ("survey_id", "in", [technical_survey.id, logical_survey.id, emotional_survey.id]),
        ("applicant_id", "=", applicant.id),
        ("state", "!=", "done"),
    ], limit=1)
    if pending_any:
        applicant.message_post(body="Assessments not sent because pending assessment links already exist for this applicant.")
        continue

    deadline = datetime.datetime.now() + datetime.timedelta(days=deadline_days)

    # Get or create answers (sample logic, no def)
    technical_test = env["survey.user_input"].search([
        ("survey_id", "=", technical_survey.id),
        ("partner_id", "=", applicant.partner_id.id),
        ("applicant_id", "=", applicant.id),
    ], limit=1)
    if not technical_test:
        technical_test = technical_survey._create_answer(partner=applicant.partner_id, applicant_id=applicant.id, deadline=deadline)

    logical_test = env["survey.user_input"].search([
        ("survey_id", "=", logical_survey.id),
        ("partner_id", "=", applicant.partner_id.id),
        ("applicant_id", "=", applicant.id),
    ], limit=1)
    if not logical_test:
        logical_test = logical_survey._create_answer(partner=applicant.partner_id, applicant_id=applicant.id, deadline=deadline)

    emotional_test = env["survey.user_input"].search([
        ("survey_id", "=", emotional_survey.id),
        ("partner_id", "=", applicant.partner_id.id),
        ("applicant_id", "=", applicant.id),
    ], limit=1)
    if not emotional_test:
        emotional_test = emotional_survey._create_answer(partner=applicant.partner_id, applicant_id=applicant.id, deadline=deadline)

    local_context = dict(
        technical_test=technical_test.get_start_url(),
        logical_test=logical_test.get_start_url(),
        emotional_test=emotional_test.get_start_url(),
        deadline=deadline,
        default_subject="Next Steps for the %s Position at %s" % (
            (job.name or "Your Applied Job"),
            (job.company_id.name or "Our Company"),
        ),
    )

    mail_id = template.with_context(local_context).send_mail(applicant.id, force_send=False)

    if mail_id:
        mail = env["mail.mail"].browse(mail_id)
        applicant.message_post(
            subtype_xmlid="mail.mt_note",
            body=(
                "<b>Assessment email queued</b><br/>"
                f"<b>To:</b> {mail.email_to or ''}<br/>"
                f"<b>Subject:</b> {mail.subject or ''}<br/><br/>"
                f"{mail.body_html or ''}"
            ),
        )
    # Move stage and block (no extra checks)
    stage = env["hr.recruitment.stage"].search([
        ("name", "=", "Assessment Sent"),
        ("job_ids", "in", [job.id]),
    ], limit=1)
    if not stage:
        stage = env["hr.recruitment.stage"].search([("name", "=", "Assessment Sent")], limit=1)

    vals = {"kanban_state": "blocked"}
    if stage:
        vals["stage_id"] = stage.id
    applicant.write(vals)

    applicant.message_post(body="Assessments sent by email. Applicant moved to Assessment Sent and marked as blocked.")

for record in records:
    if not record.partner_id:
        if not record.partner_name:
            raise UserError(_('Please provide an applicant name.'))
        action = { record.partner_id: env['res.partner'].sudo().create({
            'is_company': False,
            'name': record.partner_name,
            'email': record.email_from,
            'phone': record.partner_phone,
            'mobile': record.partner_mobile
        })
        }

    record.job_id.survey_id.check_validity()
    record.job_id.x_studio_emotional_assessment.check_validity()
    record.job_id.x_studio_logical_assessment.check_validity()

    def _get_or_create_answer(survey):
        """Return an existing user_input if found, otherwise create a new one."""
        # Search for existing user_input for this survey + partner + applicant
        existing_answer = env['survey.user_input'].search([
            ('survey_id', '=', survey.id),
            ('partner_id', '=', record.partner_id.id),
            ('applicant_id', '=', record.id),
        ], limit=1)
        if existing_answer:
            return existing_answer
        # Otherwise, create a new one
        return survey._create_answer(
            partner=record.partner_id,
            applicant_id=record.id,
            deadline=datetime.datetime.now() + datetime.timedelta(days=7)
        )

    # Retrieve or create each assessment
    technical_test = _get_or_create_answer(record.job_id.survey_id)
    logical_test = _get_or_create_answer(record.job_id.x_studio_logical_assessment)
    emotional_test = _get_or_create_answer(record.job_id.x_studio_emotional_assessment)


    #technical_test = record.job_id.survey_id._create_answer(partner=record.partner_id, applicant_id=record.id, deadline=datetime.datetime.now() + datetime.timedelta(days=7))
    #logical_test = record.job_id.x_studio_logical_assessment._create_answer(partner=record.partner_id, applicant_id=record.id, deadline=datetime.datetime.now() + datetime.timedelta(days=7))
    #emotional_test = record.job_id.x_studio_emotional_assessment._create_answer(partner=record.partner_id, applicant_id=record.id, deadline=datetime.datetime.now() + datetime.timedelta(days=7))

    template = env.ref('mail_template_recruitment.mail_template_applicant_multi_test', raise_if_not_found=False)
    local_context = dict(
        default_applicant_id=record.id,
        default_partner_ids=record.partner_id.ids,
        default_survey_id=record.survey_id.id,
        default_use_template=bool(template),
        default_template_id=template and template.id or False,
        default_email_layout_xmlid='mail.mail_notification_light',
        default_deadline=datetime.datetime.now() + datetime.timedelta(days=7),
        technical_test = technical_test.get_start_url(),
        logical_test = logical_test.get_start_url(),
        emotional_test = emotional_test.get_start_url(),
        deadline = datetime.datetime.now() + datetime.timedelta(days=7),
        default_subject = "Next Steps for the {job} Position at {company}".format(
           job=record.job_id.name or "Your Applied Job",
            company=record.job_id.company_id.name or "Our Company"
        ),

    )

    action = {
        'type': 'ir.actions.act_window',
        'name': "Send an interview",
        'view_mode': 'form',
        'res_model': 'survey.invite',
        'target': 'new',
        'context': local_context,
    }
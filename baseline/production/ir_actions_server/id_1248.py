for record in records:

    # Ensure partner exists
    if not record.partner_id:
        if not record.partner_name:
            raise UserError(_('Please provide an applicant name.'))

        partner = env['res.partner'].sudo().create({
            'is_company': False,
            'name': record.partner_name,
            'email': record.email_from,
            'phone': record.partner_phone,
            'mobile': record.partner_mobile,
        })

        # IMPORTANT: use write(), not record.partner_id = ...
        record.sudo().write({'partner_id': partner.id})

    # Technical survey for the current job position
    technical_survey = record.job_id.survey_id
    if not technical_survey:
        raise UserError(_('No Technical Assessment is configured for this Job Position.'))

    technical_survey.check_validity()

    deadline = datetime.datetime.now() + datetime.timedelta(days=7)

    # Get or create the technical assessment answer
    technical_test = env['survey.user_input'].search([
        ('survey_id', '=', technical_survey.id),
        ('partner_id', '=', record.partner_id.id),
        ('applicant_id', '=', record.id),
    ], limit=1)

    if not technical_test:
        technical_test = technical_survey._create_answer(
            partner=record.partner_id,
            applicant_id=record.id,
            deadline=deadline
        )

    template = env.ref('hr_recruitment_survey.mail_template_applicant_only_technical', raise_if_not_found=False)

    local_context = dict(
        default_applicant_id=record.id,
        default_partner_ids=record.partner_id.ids,
        default_survey_id=technical_survey.id,
        default_use_template=bool(template),
        default_template_id=template and template.id or False,
        default_email_layout_xmlid='mail.mail_notification_light',
        default_deadline=deadline,
        technical_test=technical_test.get_start_url(),
        deadline=deadline,
        default_subject="Next Step: Complete Your Assessment for {job}".format(
            job=record.job_id.name or "Your Application"
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


# Refuse v2 — clean send_mail() path
# Bypasses applicant.get.refuse.reason._prepare_mail_values which doesn't render email_from
for wizard in records:
    if not wizard.refuse_reason_id:
        raise UserError("Pick a refuse reason first.")

    applicant_ids = wizard.applicant_ids.with_context(active_test=False).ids
    template = wizard.refuse_reason_id.template_id

    env['hr.applicant'].browse(applicant_ids).write({
        'refuse_reason_id': wizard.refuse_reason_id.id,
        'active': False,
        'refuse_date': datetime.datetime.now(),
    })

    if wizard.send_mail and template:
        for app_id in applicant_ids:
            template.send_mail(app_id, force_send=False, email_layout_xmlid=template.email_layout_xmlid or False)

action = {'type': 'ir.actions.act_window_close'}

# Available variables:
#  - env: environment on which the action is triggered
#  - model: model of the record on which the action is triggered; is a void recordset
#  - record: record on which the action is triggered; may be void
#  - records: recordset of all records on which the action is triggered in multi-mode; may be void
#  - time, datetime, dateutil, timezone: useful Python libraries
#  - float_compare: utility function to compare floats based on specific precision
#  - b64encode, b64decode: functions to encode/decode binary data
#  - log: log(message, level='info'): logging function to record debug information in ir.logging table
#  - _logger: _logger.info(message): logger to emit messages in server logs
#  - UserError: exception class for raising user-facing warning messages
#  - Command: x2many commands namespace
# To return an action, assign: action = {...}

for applicant in records:
    if applicant.stage_id.id == 7 and applicant.kanban_state != 'blocked':
        overdue_survey = env['survey.user_input'].search([
            ('applicant_id', '=', applicant.id),
            ('state', '!=', 'done'),
            ('deadline', '<', datetime.datetime.now())
        ], limit=1)
        if overdue_survey:
            applicant.message_post(body="Didn't complete Assessment – Survey expired")
            email_template = env['mail.template'].browse(68)
            if email_template:
                # Send the email
                res = email_template.send_mail(applicant.id, force_send=False)
                # Extract the generated email body from mail.mail
                mail_record = env['mail.mail'].search([
                    ('mail_message_id', '=', res)
                ], order="id desc", limit=1)

                if mail_record and mail_record.body_html:
                    # Post the rendered email content in the chatter
                    applicant.message_post(body=mail_record.body_html)

                #email_template.with_context(force_send=True).message_post_with_template(68, email_layout_xmlid='mail.mail_notification_light')
            applicant.write({
                'refuse_date': datetime.datetime.now().date(),
                'refuse_reason_id': 11,
                'kanban_state': 'blocked',
                'active': False

            })
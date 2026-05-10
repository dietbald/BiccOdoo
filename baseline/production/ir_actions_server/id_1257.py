for record in records:
    template = env.ref('__custom__.recruitment_interview_invite', raise_if_not_found=False)            
    template.send_mail(
                    record.id, force_send=True,
                    email_values={'model': record._name, 'res_id': record.id},
                    email_layout_xmlid='mail.mail_notification_light')
                    
    for user in record.interviewer_ids:
        record.activity_schedule(
                            activity_type_id=25,
                            user_id=user.id
                        )
    
    



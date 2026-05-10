record.write({
    'email_from': record.partner_id.email if record.partner_id else False
})

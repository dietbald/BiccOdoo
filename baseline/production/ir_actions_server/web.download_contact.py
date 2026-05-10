
            action = {
                'type': 'ir.actions.act_url',
                'url': '/web/partner/vcard?partner_ids=' + ','.join(map(str, records.ids)),
                'target': 'download',
            }
        
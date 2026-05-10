
mapping = {1: 7, 2: 6}
for record in records:
    if not record.alias_id or not record.company_id:
        continue
    target = mapping.get(record.company_id.id)
    if target and record.alias_id.alias_domain_id.id != target:
        record.alias_id.write({'alias_domain_id': target})

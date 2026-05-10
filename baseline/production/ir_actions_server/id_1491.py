# Loop through the recordset provided by the Server Action
for record in records:
    record.write({'state': 'draft'})

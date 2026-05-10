
if records:
    action = records.filtered(lambda asset: asset.state == 'draft').validate()
        
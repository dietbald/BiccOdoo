
if records:
    action = records.filtered(lambda asset: asset.state == 'draft').compute_depreciation_board()
        
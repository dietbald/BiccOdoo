lost_reason_code = record.x_studio_lost_reason_code
won_status = record.won_status
stage = record.stage_id

bid_results = False

# 1. Lost has highest priority
if lost_reason_code:
    bid_results = lost_reason_code

# 2. Won
elif won_status == "won" or (stage and stage.name == "Opportunity Won"):
    bid_results = "WON"

# 3. Otherwise Open
else:
    bid_results = "OPEN"

record.update({
    'x_studio_bid_results': bid_results
})

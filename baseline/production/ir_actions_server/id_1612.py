for so in records:
    if so.opportunity_id:
        so.opportunity_id.write({
            "x_studio_quotation_linked_to_opportunity": so.id
        })


            action = model.with_context(
                search_default_filter_to_reorder=True,
                search_default_filter_not_snoozed=True,
                default_trigger='manual',
                searchpanel_default_trigger='manual'
            ).action_open_orderpoints()
        
for contract in records:
    # Skip if no start date
    if not contract.date_start:
        continue

    # Add 6 months to the start date
    new_end = contract.date_start + dateutil.relativedelta.relativedelta(months=6)

    # Update the contract end date
    contract.write({"date_end": new_end})

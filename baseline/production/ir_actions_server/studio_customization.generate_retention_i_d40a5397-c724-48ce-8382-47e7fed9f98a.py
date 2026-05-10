if record.x_studio_retention_withheld and record.x_studio_retention_withheld > 0:
    product = env['product.product'].search([('name', '=', 'Retention (Project)')], limit=1)
    if not product:
        raise UserError("Product 'Retention (Project)' not found.")

    # Step 1: Optional - Create sale order line if needed
    retention_sol = env['sale.order.line'].create({
        'order_id': record.id,
        'product_id': product.id,
        'product_uom_qty': 1,
        'price_unit':  record.x_studio_retention_withheld,
        'qty_delivered': 1,
        'qty_invoiced': 1,
        'name': f"Retention for {record.name}",
    })

    # Step 2: Create invoice
    inv_vals = {
        'move_type': 'out_invoice',
        'partner_id': record.partner_id.id,
        'invoice_origin': record.name or False,
        'invoice_date': datetime.date.today(),
        'currency_id': record.currency_id.id,
        'x_studio_invoice_tag': [(6, 0, [4])],
        'invoice_line_ids': [(0, 0, {
            'product_id': product.id,
            'quantity': 1,
            'price_unit': record.x_studio_retention_withheld,
            'name': f"Release of Retention for {record.name}",
            'sale_line_ids': [(6, 0, [retention_sol.id])],
            'analytic_distribution': {record.project_id.account_id.id: 100.0} if record.project_id.account_id else {},
            'tax_ids': [(6, 0, [])]
        })],
    }

    inv = env['account.move'].create(inv_vals)

    action = {
        "type": "ir.actions.act_window",
        "res_model": "account.move",
        "res_id": inv.id,
        "view_mode": "form",
        "target": "current",
    }
else:
    raise UserError("No retained amount to invoice.")



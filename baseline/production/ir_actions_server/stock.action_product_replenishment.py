
                for record in records:
                    if record.type == 'consu':
                        action = {
                            "name": "Low on stock? Let's replenish.",
                            "type": "ir.actions.act_window",
                            "res_model": "product.replenish",
                            "context": {'default_product_id': records.id},
                            "views": [[False, "form"]],
                            "target": "new",
                        }
                    else:
                        raise UserError(env._("Replenishment is only available for inventory-managed products."))
            
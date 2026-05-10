
            if records:
                records.with_context(payslip_generate_pdf=True).action_payslip_done()
        
from odoo import fields, models, _

class WizardDate(models.TransientModel):
    _name = "wizard.date"
    _description = "Wizard date"

    invoice_date_time = fields.Datetime(string="Invoice Date")

    def button_create(self):
        record_ids = self._context.get('active_ids')
        move = self.env['account.move'].browse(record_ids)
        move.write({
            'invoice_date_time':self.invoice_date_time,
            'invoice_date':self.invoice_date_time.date()
        })







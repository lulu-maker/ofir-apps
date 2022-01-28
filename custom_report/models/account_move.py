from odoo import api, fields, models, _

class accountMove(models.Model):
    _inherit = "account.move"

    seller_id = fields.Many2one('res.partner', string="Seller")
    invoice_date_time = fields.Datetime(string="Invoice Date")
    delivery_date_time = fields.Date(string="Datum Dostave")

    def _post(self, soft=True):
        self.invoice_date = fields.Date.context_today(self)
        posted = super()._post(soft)
        return posted

    # def action_post(self):
    #     is_date = False
    #     if not self.invoice_date:
    #         is_date = True
    #     res = super(accountMove, self).action_post()
    #     if is_date:
    #         self.write({
    #             'invoice_date':False
    #         })
    #     return False
from odoo import api, fields, models, _

class resCompany(models.Model):
    _inherit = "res.company"

    iban = fields.Char(string="IBAN")
    description = fields.Char(string="Description")
    sjedište = fields.Text(string="Sjedište")
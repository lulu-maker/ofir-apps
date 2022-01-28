# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source ERP and CRM
#    Author: Uvid d.o.o.
#    Copyright: Uvid d.o.o.
#    web: https://odoo.com.hr/
#    e-mail: info@uvid.hr
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, fields, models, _

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    working_place_id = fields.Many2one('working.place', string='Working Place',)
    payment_type = fields.Selection([('G','Cash'), ('K','Credit card'), ('C','Cheque'), ('T','Transaction account'), ('O', 'Other')], string='Payment Type')

    @api.onchange('working_place_id')
    def onchange_working_place_id(self):
        inv_journal_types = self.env['account.move'].get_invoice_types(include_receipts=True)
        if self.type in inv_journal_types:
            domain = [
                ('journal_id', '=', self.id),
                ('state', '=', 'posted')
            ]
            if self.env['account.move'].search_count(domain):
                warning = { 'title': _('Warning'), 'message': _('Do not change working place on journals that have been invoiced !'), 'type': 'notification'}
                res.update(warning=warning)
                return res

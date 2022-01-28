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
from odoo.exceptions import ValidationError
from time import strftime

class AccountMoveWizard(models.TransientModel):
    _name = "account.move.wizard"
    _description = "Subsequent Fiscalization"

    check = fields.Boolean(string = 'Check this box', required = True, default=False)

    def check_invoice(self):
        if not self.env.user.company_id.use_fiscalization or not self._context.get('active_id'):
            return {'type': 'ir.actions.act_window_close'}

        invoice_id = self.env.context['active_id']
        invoice_obj = self.env['account.move'].browse(invoice_id)

        action = self.check
        if invoice_obj.fisc_state == 'done':
            raise ValidationError(_('Invoice already sent!'))

        if invoice_obj.state != 'posted':
            raise ValidationError(_('Invoice must be posted!'))

        if action:
            invoice_obj.write({'fisc_date': strftime('%Y-%m-%d %H:%M:%S')})
            invoice_obj.do_fiscal()

        return {'type': 'ir.actions.act_window_close'}

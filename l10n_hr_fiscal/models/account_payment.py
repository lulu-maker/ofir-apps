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

class AccountPaymentRegister(models.TransientModel):

    _inherit = 'account.payment.register'

    # def post(self):
    #     super(AccountPayment, self).post()
    #     if self.invoice_ids:
    #         self.invoice_ids.do_fiscal()
    #

    def action_create_payments(self):
        res = super(AccountPaymentRegister, self).action_create_payments()

        if self.env.context.get('active_model') == 'account.move' and self.env.context.get('active_ids'):
            ai_obj = self.env['account.move']
            ai_ids = self.env.context.get('active_ids')

            for ai in ai_obj.browse(ai_ids):
                if ai.payment_state == 'paid':
                    ai.do_fiscal()

        return res


    # TODO: provjeri jel iznos placanja odgovara (nema preplate)
    # @api.constrains('amount')
    # def _check_amount(self):
    #     # super(AccountPayment, self)._check_amount()
    #
    #     for payment in self:
    #         if payment.amount > payment.invoice_ids.amount_residual:
    #             raise ValidationError(_('The payment amount cannot exceed residual amount of the invoice.'))

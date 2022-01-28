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
from pytz import timezone
import datetime
import uuid
import os
import base64

class Company(models.Model):
    _inherit='res.company'

    use_fiscalization = fields.Boolean(string='Use fiscalization?', default=False)
    certificate = fields.Binary(string='Certificate PFX')
    certificate_pass = fields.Char(string='Certificate password', size=64)
    certificate_pem = fields.Binary(string='Certificate PEM')
    certificate_key = fields.Binary(string='Certificate KEY')
    server_address = fields.Char(string='Server address', size=64)
    server_port = fields.Char(string='Server port', size=8)
    service_name = fields.Char(string='WEB Service name', size=64)
    vat_system = fields.Selection([('yes','Yes'), ('no', 'No')], string='In VAT system', required=True, default='yes')
    count_system = fields.Selection([('P','By Shop'), ('N', 'By Enu')], string='Count system', required=True, default='P')
    echo_message = fields.Char('Echo Message', readonly=True, copy=False)

    def write(self, values):
        if values.get('certificate', False):
            if not self.browse(self.env.company.id).certificate_pass and not values.get('certificate_pass', False):
                raise osv.except_osv(_('Error'),_('Password is required for converting the certificate file!'))
            password = ""
            if values.get('certificate_pass', False):
                password = values['certificate_pass']
            else:
                password = self.browse(self.env.company.id).certificate_pass

            cert = values['certificate']
            cert_decoded = base64.b64decode(cert)
            filename = uuid.uuid1()
            fn = open('/tmp/' + str(filename) + '.pfx', 'wb')
            fn.write(cert_decoded)
            fn.close()

            os.system('openssl pkcs12 -in /tmp/' + str(filename) + '.pfx -out /tmp/' + str(filename) + '.pem -nodes -passin pass:' + password)
            fn = open('/tmp/' + str(filename) + '.pem', 'rb')
            cert_pem = fn.read()
            cert = base64.b64encode(cert_pem)
            values.update({'certificate_pem': cert})
            fn.close()

            os.system('openssl rsa -in /tmp/' + str(filename) + '.pem -out /tmp/' + str(filename) + '.key')
            fn = open('/tmp/' + str(filename) + '.key', 'rb')
            cert_key = fn.read()
            key = base64.b64encode(cert_key)
            values.update({'certificate_key': key})
            fn.close()

            os.system('rm /tmp/' + str(filename) + '.pfx')
            os.system('rm /tmp/' + str(filename) + '.pem')
            os.system('rm /tmp/' + str(filename) + '.key')
        return super(Company, self).write(values)

    def button_test_echo(self, context=None):
        pass
        # if context is None:
        #     context = {}
        #
        # res = datetime.datetime.now(timezone('Europe/Zagreb')).strftime("%Y-%m-%d %H:%M:%S")
        # test_message = 'Test fiscalization!'
        # echo = self.env['fiscalization.hr'].soap_message_send(test_message)
        #
        # try:
        #     echo_reply = echo.execute()
        #     if (echo_reply != False):
        #         res += ' Fiscalization ECHO test successful!'
        #     else:
        #         errors = echo.get_last_error()
        #         res += ' '
        #         for error in errors:
        #             res += error + "\n"
        # except Exception as e:
        #     res += ' ' + str(e)
        #
        # self.write({'echo_message': res})
        #
        # return True

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

{
    'name': 'Croatian Fiscalization',
    'version': '0.9',
    'author': 'Uvid d.o.o.',
    'website': 'https://odoo.com.hr',
    "license": "",
    "price": 199.99,
    "currency": 'EUR',
    'category': 'Accounting/Accounting',
    'sequence': 1,
    'summary': 'Fiscalization - HR',
    'description': 'Fiscalization of Invoices - Croatian version',
    'depends': [
        'account',
        'base'
    ],
    'external_dependencies': {
        'python': ['M2Crypto', 'signxml']
    },
    'data': [
        'security/ir.model.access.csv',
        'views/res_company.xml',
        'views/account_move.xml',
        'views/working_place.xml',
        'views/account_journal.xml',
        'views/account_tax.xml',
        'wizard/invoice_fisc_wizard.xml',
        'report/report_invoice.xml',
    ],
    'demo': [],
    'test': [],
    'css': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'images': ['images/main_screenshot.png'],
}

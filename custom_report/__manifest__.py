# -*- coding: utf-8 -*-
{
    'name': "Odoo Custom Reposts",
    'application': False,
    'author': "Bansi Babariya",
    'auto_install': False,
    'category': "Extra Tools",
    'data': [
        'security/ir.model.access.csv',
        'wizard/wizard_date.xml',
        'views/account_move_view.xml',
        'views/res_company_view.xml',
        'report/report_paperformat.xml',
        'report/report.xml',
        'report/sale_report_templates.xml',
        'report/invoice_report_templates.xml',
    ],
    'demo': [],
    'depends': [
        'sale_management', 'account'
    ],
    'qweb': [
     ],
    'description': "Odoo Custom Reports",
    'installable': True,
    'summary': "Custom Reports",
    'test': [],
    'version': "14.0.1",
}

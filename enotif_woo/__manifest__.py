{
    'name': "Enotif WooCommerce",
    'version': '14.0.1.0.0',
    'summary': """Connects the External Notifications module to WooCommerce""",
    'description': """
       Provides methods to connect the "External Notifications" module to a WooCommerce website.
       Requires "External Notifications" Odoo module and "Notify Odoo" WordPress plugin on the WooCommerce website.
       This module will be used by other modules like "Enotif WooCommerce Customer" to get customers from WooCommerce.                          
    """,
    'author': 'Pektsekye',
    'category': 'Website',
    'depends': ['enotif'],
    'data': [ 
        'security/ir.model.access.csv',                              
        'views/view.xml',
        'data/connection.xml'        
    ],
    'demo': [],
    'images': ['static/description/screenshots/ScreenShot.png'],    
    'license': 'LGPL-3',
    'application': False,    
    'installable': True,
    'auto_install': True,
}

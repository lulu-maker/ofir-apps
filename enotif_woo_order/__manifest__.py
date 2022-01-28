{
    'name': "Enotif WooCommerce Order",
    'version': '14.0.1.0.0',
    'summary': """Receives notifications of new WooCommerce orders""",
    'description': """
       Receives notifications of new WooCommerce orders and saves them.
       Requires "Enotif WooCommerce" module.
       To save a new customer requires the "Enotif WooCommerce Customer" module.
       Without this module will save the new order with a default customer.                          
    """,
    'author': 'Pektsekye',
    'category': 'Website',
    'depends': ['enotif_woo',                
                ],
    'data': [
        'security/ir.model.access.csv',
        'data/notification_types.xml',                           
        'views/view.xml'
    ],
    'demo': [], 
    'images': ['static/description/screenshot_5.png'],       
    'license': 'OPL-1',
    'application': False,    
    'installable': True,
    'auto_install': True,
}

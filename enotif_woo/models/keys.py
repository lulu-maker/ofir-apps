
from odoo import fields, models

class Keys(models.Model):
    _description = 'Enotif WooCommerce - keys model'
    _name = 'enotif_woo.keys'

    woocommerce_url = fields.Char(string='WooCommerce URL', help='WooCommerce URL')    
    woocommerce_api_key = fields.Char(string='WooCommerce API key', help='WooCommerce API Key')
    woocommerce_api_secret = fields.Char(string='WooCommerce API secret', help='WooCommerce API Secret')


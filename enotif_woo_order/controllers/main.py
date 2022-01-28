
from odoo import http
from odoo.http import request

class Customer(http.Controller):

                        
    @http.route(['/enotif_woo_order/import_orders/'], type="json", methods=['POST', 'GET'], auth="user", website=True)
    def import_customers(self, **kw):
 
        result = request.env['enotif_woo_order.order'].import_orders()

        return result

    @http.route(['/enotif_woo_order/import_customers/'], type="json", methods=['POST', 'GET'], auth="user",
                website=True)
    def import_woo_customers(self, **kw):
        print("\n\n================import_woo_customers=========BEFORE===========")
        result = request.env['enotif_woo_order.order'].import_customers()
        print("\n\n================import_woo_customers=========LAST===========",result)
        return result

    @http.route(['/enotif_woo_order/import_products/'], type="json", methods=['POST', 'GET'], auth="user",
                website=True)
    def import_woo_products(self, **kw):
        print("\n\n================import_woo_products=========BEFORE===========")
        result = request.env['enotif_woo_order.order'].import_products()
        print("\n\n================import_woo_products=========LAST===========", result)
        return result

        
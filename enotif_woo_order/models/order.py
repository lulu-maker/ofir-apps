import logging
import requests,json
from odoo import fields, models
from traceback import format_exception_only
from datetime import datetime

_logger = logging.getLogger(__name__)

WOOCOMMERCE_API_ORDERS_PATH = '/wp-json/wc/v3/orders/'
WOOCOMMERCE_API_CUSTOMERS_PATH = '/wp-json/wc/v3/customers'
WOOCOMMERCE_API_PRODUCTS_PATH = '/wp-json/wc/v3/products'
URLOPEN_TIMEOUT = 30

ORDER_CODE_PREFIX = 'wc_order_'


class Order(models.AbstractModel):
    _description = 'Enotif WooCommerce Orders - order model'
    _name = 'enotif_woo_order.order'

    def process_notifications(self, notification_type, item_ids):

        processed_ids = []

        if notification_type == 'new_order':

            result = self.fetch_orders(item_ids)
            if 'error' in result:  # cannot get data from remote website. try again on the next cron job
                return []

            orders = result['orders']

            fetched_ids = set()
            for data in orders:
                order_id = data['id']
                fetched_ids.add(order_id);
            not_fetched_ids = [id for id in item_ids if id not in fetched_ids]
            # some items do not exist on the remote website. delete notifications about them
            processed_ids.extend(not_fetched_ids);

            for data in orders:
                order_id = data['id']
                try:
                    self.add_order(data)
                    processed_ids.append(order_id);
                except Exception as e:
                    _logger.error(
                        "ERROR: Enotif WooCommerce Order module cannot pocess notification type: %s \n item_id: %s  \n error text: %s",
                        notification_type, order_id, format_exception_only(type(e), e))

        else:  # unknown notification type
            processed_ids.extend(item_ids);

        return processed_ids

    def add_order(self, data):

        #   state = fields.Selection([
        #        ('draft', 'Quotation'),
        #        ('sent', 'Quotation Sent'),
        #        ('sale', 'Sales Order'),
        #        ('done', 'Locked'),
        #        ('cancel', 'Cancelled'),
        # optional fields
        #              'pricelist_id': request.env.ref('product.list0').id,
        #              'partner_invoice_id': request.env.ref('base.res_partner_address_25').id,
        #              'partner_shipping_id': request.env.ref('base.res_partner_address_25').id,
        #              'confirmation_date' : (datetime.now()-timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S'),

        partner_id = self.env.ref('base.public_partner').id
        billing_info = data.get('billing', {})
        if billing_info:
            email = billing_info.get('email', '').strip()
            partner = self.env['res.partner'].search([('email', '=', email)], limit=1)
            if partner:
                partner_id = partner.id
            else:
                Customer = self.env.get('enotif_woo_customer.customer')
                if Customer is not None:
                    result = Customer.add_customer({'first_name': billing_info.get('first_name', ''),
                                                    'last_name': billing_info.get('last_name', ''), 'email': email,
                                                    'billing': billing_info, 'shipping': data.get('shipping', {})})
                    if 'partner_id' in result:
                        partner_id = result['partner_id']

        date_created = data.get('date_created', '')
        if date_created:
            date_created = date_created.replace('T', ' ')  # '2019-08-26T21:53:49' -> '2019-08-26 21:53:49'
        else:
            date_created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        new_order_name = ORDER_CODE_PREFIX + data.get('number', '')

        record = self.env['sale.order'].search([('name', '=', new_order_name)], limit=1)
        if record:
            _logger.warning("Enotif Woocommerce Order cannot create new order. Order with code \"%s\" already exists.",
                            new_order_name)
            return

        order = self.env['sale.order'].create({
            'name': new_order_name,
            'create_date': datetime.now(),
            'partner_id': partner_id,
            'user_id': self.env.ref('base.default_user').id,
            'team_id': self.env.ref('sales_team.salesteam_website_sales').id,
            'date_order': date_created,
            'state': 'sale'
        })

        if order.id:
            line_items = data.get('line_items', [])
            if line_items:
                for item in line_items:
                    sku = item.get('sku', '').strip()
                    if not sku:
                        sku = 'imported_product_' + str(item.get('product_id', ''))
                    record = self.env['product.product'].search([('default_code', '=', sku)], limit=1)
                    if not record:
                        record = self.env['product.product'].create(
                            {'name': item.get('name', ''), 'default_code': sku, 'list_price': item.get('price', 0.0),
                             'type': 'service'})
                    order_line = self.env['sale.order.line'].create({
                        'order_id': order.id,
                        'name': item.get('name', ''),
                        'product_id': record.id,
                        'product_uom_qty': item.get('quantity', 1),
                        'product_uom': self.env.ref('uom.product_uom_unit').id,
                        'price_unit': item.get('price', 0.0)
                    })

    def fetch_orders(self, order_ids=[], params={}):
        """
          url = 'https://hottons.com/demo/wp/odp/wp-json/wc/v3/orders/?include=501,503&consumer_key=111111&consumer_secret=222222'
          result = [{"id":4,"date_created":"2018-07-24T09:54:49"}]
        """

        record = self.env['enotif_woo.keys'].search([], limit=1)
        if not record.id:
            error_text = "Enotif WooCommerce Order module cannot get data via WooCommerce API because the WooCommerce URL is not specified. Please set WooCommerce URL in Odoo admin panel -> Menu -> External Notifications -> WooCommerce Keys"
            _logger.warning(error_text)
            return {'error': 1, 'error_text': error_text}

        woocommerce_url = record.woocommerce_url
        woocommerce_api_key = record.woocommerce_api_key
        woocommerce_api_secret = record.woocommerce_api_secret

        result = {};

        url = woocommerce_url.rstrip("/") + WOOCOMMERCE_API_ORDERS_PATH

        if not params:
            order_ids_str = ','.join(str(e) for e in order_ids)
            params = {'include': order_ids_str, 'per_page': 100}

        headers = {'User-Agent': 'odoo_enotif_request'}
        keys = (woocommerce_api_key, woocommerce_api_secret)

        try:
            r = requests.get(url, params=params, auth=keys, headers=headers, timeout=URLOPEN_TIMEOUT, verify=False)
            r.raise_for_status()
            result['orders'] = r.json()

            totalPages = int(r.headers.get('X-WP-TotalPages', 1))
            if totalPages > 1:
                for i in range(2, totalPages + 1):
                    params['page'] = i
                    r = requests.get(url, params=params, auth=keys, headers=headers, timeout=URLOPEN_TIMEOUT,
                                     verify=False)
                    result['orders'].extend(r.json())
        except Exception as e:
            error_text = "ERROR: Enotif WooCommerce Order module cannot get data via WooCommerce API with URL %s \n error text : %s" % (
            url, format_exception_only(type(e), e))
            result = {'error': 1, 'error_text': error_text}
            _logger.error(error_text)

        return result

    def fetch_customers(self):
        """
          url = 'https://hottons.com/demo/wp/odp/wp-json/wc/v3/orders/?include=501,503&consumer_key=111111&consumer_secret=222222'
          result = [{"id":4,"date_created":"2018-07-24T09:54:49"}]
        """

        record = self.env['enotif_woo.keys'].search([], limit=1)
        print("=========================record===========",record)
        if not record.id:
            error_text = "Enotif WooCommerce Order module cannot get data via WooCommerce API because the WooCommerce URL is not specified. Please set WooCommerce URL in Odoo admin panel -> Menu -> External Notifications -> WooCommerce Keys"
            _logger.warning(error_text)
            return {'error': 1, 'error_text': error_text}

        woocommerce_url = record.woocommerce_url
        woocommerce_api_key = record.woocommerce_api_key
        woocommerce_api_secret = record.woocommerce_api_secret

        result = {};

        url = woocommerce_url.rstrip("/") + WOOCOMMERCE_API_CUSTOMERS_PATH

        headers = {'User-Agent': 'odoo_enotif_request'}
        keys = (woocommerce_api_key, woocommerce_api_secret)

        try:
            r = requests.get(url, auth=keys, headers=headers, timeout=URLOPEN_TIMEOUT, verify=False)
            r.raise_for_status()
            print("=====================r.json()======================",r.json())
            result['customers'] = r.json()
        except Exception as e:
            error_text = "ERROR: Enotif WooCommerce Order module cannot get data via WooCommerce API with URL %s \n error text : %s" % (
            url, format_exception_only(type(e), e))
            result = {'error': 1, 'error_text': error_text}
            _logger.error(error_text)

        return result

    def fetch_products(self):
        """
          url = 'https://hottons.com/demo/wp/odp/wp-json/wc/v3/orders/?include=501,503&consumer_key=111111&consumer_secret=222222'
          result = [{"id":4,"date_created":"2018-07-24T09:54:49"}]
        """

        record = self.env['enotif_woo.keys'].search([], limit=1)
        print("=========================record===========",record)
        if not record.id:
            error_text = "Enotif WooCommerce Order module cannot get data via WooCommerce API because the WooCommerce URL is not specified. Please set WooCommerce URL in Odoo admin panel -> Menu -> External Notifications -> WooCommerce Keys"
            _logger.warning(error_text)
            return {'error': 1, 'error_text': error_text}

        woocommerce_url = record.woocommerce_url
        woocommerce_api_key = record.woocommerce_api_key
        woocommerce_api_secret = record.woocommerce_api_secret

        result = {};

        url = woocommerce_url.rstrip("/") + WOOCOMMERCE_API_PRODUCTS_PATH

        headers = {'User-Agent': 'odoo_enotif_request'}
        keys = (woocommerce_api_key, woocommerce_api_secret)

        try:
            r = requests.get(url, auth=keys, headers=headers, timeout=URLOPEN_TIMEOUT, verify=False)
            r.raise_for_status()
            print("=====================r.json()======products================",r.json())
            result['products'] = r.json()
        except Exception as e:
            error_text = "ERROR: Enotif WooCommerce Order module cannot get data via WooCommerce API with URL %s \n error text : %s" % (
            url, format_exception_only(type(e), e))
            result = {'error': 1, 'error_text': error_text}
            _logger.error(error_text)

        return result

    def import_orders(self):

        result = self.fetch_orders([], {'_fields': 'id,number', 'per_page': 100})
        if 'error' in result:  # cannot get data from remote website.
            return result

        orders = result['orders']

        number_of_orders = 0

        if orders:
            model_id = self.env['ir.model']._get(self._name).id

            local_order_names = set(
                self.env['sale.order'].search([('name', '=like', ORDER_CODE_PREFIX)]).mapped('name'))

            ids = [c['id'] for c in orders if ORDER_CODE_PREFIX + c['number'] not in local_order_names]

            Notification = self.env['enotif.notification']

            # set priority 10 so it will be processed after the live notifications from another website with default priority 5
            Notification.save_notifications_for_type('new_order', ids, priority=10)

            Notification.schedule_fetch_notifications_cron_job()

            number_of_orders = len(ids)

        return {'number_of_orders': number_of_orders}

    def import_customers(self):
        result = self.fetch_customers()
        if 'error' in result:  # cannot get data from remote website.
            return result
        customers = result['customers']
        number_of_customers = 0
        if customers:
            # print("=========customers========",json.dumps(customers, indent = 3))
            for customer in customers:
                print("\n=========customers========", json.dumps(customer, indent=3))
                if customer.get('email'):
                    exist_customer = self.env['res.partner'].sudo().search([('email','=',customer.get('email'))])
                    if not exist_customer:
                        customer_obj = self.env['res.partner'].sudo().create({
                            'name': customer.get('first_name') + ' ' + customer.get('last_name'),
                            'email': customer.get('email'),
                        })
                        print("\n=========customer_obj========", customer_obj)
            number_of_customers = len(customers)

        return {'number_of_customers': number_of_customers}

    def import_products(self):
        result = self.fetch_products()
        if 'error' in result:  # cannot get data from remote website.
            return result
        products = result['products']
        number_of_products = 0
        if products:
            # print("=========customers========",json.dumps(customers, indent = 3))
            for product in products:
                print("\n=========products========", json.dumps(product, indent=3))
                if product.get('name'):
                    exist_product = self.env['product.template'].sudo().search([('name','=',product.get('name'))])
                    if not exist_product:
                        product_obj = self.env['product.template'].sudo().create({
                            'name': product.get('name'),
                            'list_price': product.get('price'),
                        })
                        print("\n=========product_obj========", product_obj)
            number_of_products = len(products)

        return {'number_of_products': number_of_products}
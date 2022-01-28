import logging
import base64
import json
import requests
from odoo import fields, http
from odoo.http import request
from traceback import format_exception_only

_logger = logging.getLogger(__name__)

class Connection(http.Controller):
                     
    @http.route(['/enotif_woo/init'], type='json', auth="user", website=True)
    def get_init_data(self):
        record = request.env['enotif_woo.keys'].search([],limit=1)
        data = {'woocommerceUrl':record.woocommerce_url, 'woocommerceApiKey':record.woocommerce_api_key, 'woocommerceApiSecret':record.woocommerce_api_secret}              
        return data

    @http.route(['/enotif_woo/check_connection'], type='json', auth="user", website=True)
    def check_connection(self, **kw):
        woocommerce_url = kw.get('woocommerce_url')
        woocommerce_api_key = kw.get('woocommerce_api_key')
        woocommerce_api_secret = kw.get('woocommerce_api_secret') 
        
        if not woocommerce_url or not woocommerce_api_key or not woocommerce_api_secret:
          return {'error':1, 'error_text': 'ERROR: URL, API key and the API secret fields should not be empty.'}
        
        woocommerce_url = woocommerce_url.strip()
        woocommerce_api_key = woocommerce_api_key.strip()
        woocommerce_api_secret = woocommerce_api_secret.strip()
             
        result = {}
        
        url = woocommerce_url.rstrip("/") + '/wp-json/wc/v3/products/'
        params = {'_fields' : 'id,sku,stock_quantity,in_stock'}
        #url = 'https://hottons.com/demo/wp/odp/wp-json/wc/v3/products/?_fields=id,sku,stock_quantity,in_stock&consumer_key=111111&consumer_secret=222222'
        #result = [{"id":274,"sku":"APP 3924","stock_quantity":29},{"id":273,"sku":"3324","stock_quantity":988}]
        try:
          r = requests.get(url, params=params, auth=(woocommerce_api_key, woocommerce_api_secret), headers={'User-Agent': 'odoo_enotif_request'}, timeout=30, verify=False)               
          if r.status_code == requests.codes.ok:
            try:
              result['products'] = r.json()
            except:
              result['error'] = 1
              result['url'] = r.url
              result['response_content'] = r.text
              result['error_text'] = 'Response is not a valid JSON string'
          else:
            result['error'] = 1
            result['headers'] = r.headers
            result['url'] = r.url 
            result['response_content'] = r.text
            try:
              result['response_json'] = r.json()
            except:
              pass               
            result['status_code'] = r.status_code
            result['history_lines'] = r.history          
            r.raise_for_status()                       
        except Exception as e:
          result['error'] = 1
          result['url'] = result.get('url') if result.get('url') else url
          result['error_text_lines'] = format_exception_only(type(e), e)
          _logger.error("ERROR: Update Woocommerce module cannot connect to WooCommerce API with URL %s \n error text : %s", url, format_exception_only(type(e), e))            
  
        Keys = request.env['enotif_woo.keys']          
        record = Keys.search([], limit=1)
        data = {'woocommerce_url' : woocommerce_url, 'woocommerce_api_key' : woocommerce_api_key, 'woocommerce_api_secret' : woocommerce_api_secret}                
        if record.id:
          record.write(data)  
        else:
          Keys.create(data)
                
        return result
        
    @http.route(['/enotif_woo/notify/'], type="http", methods=['POST', 'GET'], auth="public", website=True)
    def new_notification(self, **kw):
 
        #request.env['enotif.notification'].sudo().fetch_notifications()

        # schedule cron job to start in a minute and fetch notifications
        request.env['enotif.notification'].sudo().schedule_fetch_notifications_cron_job()

              
        if kw.get('img'): # the request is from the tracking image HTML tag <img >
          mimetype = 'image/gif'
          content = base64.b64decode('R0lGODlhAQABAIAAAP///////yH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==')
          return request.make_response(content, [('Content-Type', mimetype)])
        
        return '5'
















        